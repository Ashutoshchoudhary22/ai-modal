"""Repository intelligence MySQL persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_platform_shared.db.models import (
    RepositoryFileORM,
    RepositoryImportORM,
    RepositoryIndexRunORM,
    RepositorySymbolORM,
)


class RepositoryIndexRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_file_hashes(self, workspace_id: str) -> dict[str, str]:
        rows = self._session.scalars(
            select(RepositoryFileORM).where(RepositoryFileORM.workspace_id == workspace_id)
        ).all()
        return {row.relative_path: row.sha256 for row in rows}

    def get_latest_run(self, workspace_id: str) -> RepositoryIndexRunORM | None:
        return self._session.scalar(
            select(RepositoryIndexRunORM)
            .where(RepositoryIndexRunORM.workspace_id == workspace_id)
            .order_by(RepositoryIndexRunORM.started_at.desc())
            .limit(1)
        )

    def save_run(
        self,
        *,
        run_id: str,
        workspace_id: str,
        status: str,
        index_version: int,
        parser_version: str,
        schema_version: str,
        files_seen: int,
        files_indexed: int,
        files_skipped: int,
        files_failed: int,
        symbols_extracted: int,
        imports_extracted: int,
        duration_ms: int | None,
        error_summary: str | None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> None:
        row = RepositoryIndexRunORM(
            id=run_id,
            workspace_id=workspace_id,
            status=status,
            index_version=index_version,
            parser_version=parser_version,
            schema_version=schema_version,
            files_seen=files_seen,
            files_indexed=files_indexed,
            files_skipped=files_skipped,
            files_failed=files_failed,
            symbols_extracted=symbols_extracted,
            imports_extracted=imports_extracted,
            duration_ms=duration_ms,
            error_summary=error_summary,
            started_at=_parse_dt(started_at) if started_at else datetime.now(UTC),
            completed_at=_parse_dt(completed_at) if completed_at else None,
        )
        self._session.merge(row)
        self._session.flush()

    def remove_file(self, workspace_id: str, relative_path: str) -> None:
        normalized = relative_path.replace("\\", "/")
        self._session.execute(
            delete(RepositorySymbolORM).where(
                RepositorySymbolORM.workspace_id == workspace_id,
                RepositorySymbolORM.file_path == normalized,
            )
        )
        self._session.execute(
            delete(RepositoryImportORM).where(
                RepositoryImportORM.workspace_id == workspace_id,
                RepositoryImportORM.file_path == normalized,
            )
        )
        self._session.execute(
            delete(RepositoryFileORM).where(
                RepositoryFileORM.workspace_id == workspace_id,
                RepositoryFileORM.relative_path == normalized,
            )
        )

    def replace_file_index(
        self,
        *,
        workspace_id: str,
        file_row: dict[str, Any],
        symbols: list[dict[str, Any]],
        imports: list[dict[str, Any]],
    ) -> None:
        relative_path = file_row["relative_path"]
        self._session.execute(
            delete(RepositorySymbolORM).where(
                RepositorySymbolORM.workspace_id == workspace_id,
                RepositorySymbolORM.file_path == relative_path,
            )
        )
        self._session.execute(
            delete(RepositoryImportORM).where(
                RepositoryImportORM.workspace_id == workspace_id,
                RepositoryImportORM.file_path == relative_path,
            )
        )
        existing = self._session.scalar(
            select(RepositoryFileORM).where(
                RepositoryFileORM.workspace_id == workspace_id,
                RepositoryFileORM.relative_path == relative_path,
            )
        )
        if existing:
            for key, value in file_row.items():
                if key == "first_indexed_at":
                    continue
                setattr(existing, key, value)
        else:
            self._session.merge(RepositoryFileORM(**file_row))
        for symbol in symbols:
            self._session.merge(RepositorySymbolORM(**symbol))
        for imp in imports:
            self._session.merge(RepositoryImportORM(**imp))

    def persist_index(
        self,
        *,
        workspace_id: str,
        run: dict[str, Any],
        files: list[dict[str, Any]],
        symbols: list[dict[str, Any]],
        imports: list[dict[str, Any]],
        deleted_paths: list[str],
        changed_paths: set[str],
    ) -> None:
        for path in deleted_paths:
            self.remove_file(workspace_id, path)
        symbols_by_file: dict[str, list[dict[str, Any]]] = {}
        for symbol in symbols:
            symbols_by_file.setdefault(symbol["file_path"], []).append(symbol)
        imports_by_file: dict[str, list[dict[str, Any]]] = {}
        for imp in imports:
            imports_by_file.setdefault(imp["file_path"], []).append(imp)
        files_by_path = {file_row["relative_path"]: file_row for file_row in files}
        for path in sorted(changed_paths):
            file_row = files_by_path.get(path)
            if file_row is None:
                continue
            self.replace_file_index(
                workspace_id=workspace_id,
                file_row=file_row,
                symbols=symbols_by_file.get(path, []),
                imports=imports_by_file.get(path, []),
            )
        self.save_run(**run)

    def list_files(self, workspace_id: str) -> list[RepositoryFileORM]:
        return list(
            self._session.scalars(
                select(RepositoryFileORM)
                .where(RepositoryFileORM.workspace_id == workspace_id)
                .order_by(RepositoryFileORM.relative_path)
            ).all()
        )

    def list_symbols(self, workspace_id: str) -> list[RepositorySymbolORM]:
        return list(
            self._session.scalars(
                select(RepositorySymbolORM)
                .where(RepositorySymbolORM.workspace_id == workspace_id)
                .order_by(RepositorySymbolORM.file_path, RepositorySymbolORM.start_line)
            ).all()
        )

    def list_imports(self, workspace_id: str) -> list[RepositoryImportORM]:
        return list(
            self._session.scalars(
                select(RepositoryImportORM)
                .where(RepositoryImportORM.workspace_id == workspace_id)
                .order_by(RepositoryImportORM.file_path, RepositoryImportORM.start_line)
            ).all()
        )


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
