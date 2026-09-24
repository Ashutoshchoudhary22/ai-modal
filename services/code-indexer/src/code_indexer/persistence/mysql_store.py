"""MySQL-backed repository index persistence."""

from __future__ import annotations

from pathlib import Path

from ai_platform_shared.db import session_scope
from ai_platform_shared.db.repository_index_repository import RepositoryIndexRepository
from ai_platform_shared.db.workspace_repository import WorkspaceRepository

from code_indexer.config import INDEX_VERSION, PARSER_VERSION, SCHEMA_VERSION
from code_indexer.models import ImportRecord, IndexRun, RepositoryFile, Symbol


class IndexPersistenceError(RuntimeError):
    pass


class MySQLIndexStore:
    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id

    @staticmethod
    def is_available() -> bool:
        try:
            with session_scope() as session:
                session.connection()
            return True
        except Exception:
            return False

    def ensure_workspace(self, root: Path, *, name: str | None = None) -> None:
        normalized = str(root.resolve()).replace("\\", "/")
        try:
            with session_scope() as session:
                workspace_repo = WorkspaceRepository(session)
                existing = workspace_repo.get_by_id(self.workspace_id)
                if existing:
                    return
                by_path = workspace_repo.get_by_root_path(normalized)
                if by_path:
                    return
                workspace_repo.create_with_id(
                    workspace_id=self.workspace_id,
                    name=name or root.name,
                    root_path=normalized,
                )
        except Exception as exc:
            raise IndexPersistenceError(f"MySQL workspace setup failed: {exc}") from exc

    def load_file_hashes(self) -> dict[str, str]:
        try:
            with session_scope() as session:
                repo = RepositoryIndexRepository(session)
                return repo.get_file_hashes(self.workspace_id)
        except Exception as exc:
            raise IndexPersistenceError(f"MySQL file hash load failed: {exc}") from exc

    def persist_index(
        self,
        *,
        run: IndexRun,
        files: list[RepositoryFile],
        symbols: list[Symbol],
        imports: list[ImportRecord],
        deleted_paths: list[str],
        changed_paths: set[str],
        root: Path | None = None,
    ) -> None:
        try:
            if root is not None:
                self.ensure_workspace(root)
            with session_scope() as session:
                repo = RepositoryIndexRepository(session)
                repo.persist_index(
                    workspace_id=self.workspace_id,
                    run=_run_to_dict(run),
                    files=[
                        _file_to_row(f, self.workspace_id)
                        for f in files
                        if f.relative_path in changed_paths
                    ],
                    symbols=[_symbol_to_row(s) for s in symbols if s.file_path in changed_paths],
                    imports=[_import_to_row(i) for i in imports if i.file_path in changed_paths],
                    deleted_paths=deleted_paths,
                    changed_paths=changed_paths,
                )
        except Exception as exc:
            raise IndexPersistenceError(f"MySQL index persistence failed: {exc}") from exc

    def remove_file(self, relative_path: str) -> None:
        with session_scope() as session:
            RepositoryIndexRepository(session).remove_file(self.workspace_id, relative_path)

    def count_files(self) -> int:
        with session_scope() as session:
            return len(RepositoryIndexRepository(session).list_files(self.workspace_id))

    def count_symbols(self) -> int:
        with session_scope() as session:
            return len(RepositoryIndexRepository(session).list_symbols(self.workspace_id))

    def count_imports(self) -> int:
        with session_scope() as session:
            return len(RepositoryIndexRepository(session).list_imports(self.workspace_id))


def _run_to_dict(run: IndexRun) -> dict:
    return {
        "run_id": run.run_id,
        "workspace_id": run.workspace_id,
        "status": run.status,
        "index_version": INDEX_VERSION,
        "parser_version": PARSER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "files_seen": run.files_seen,
        "files_indexed": run.files_indexed,
        "files_skipped": run.files_skipped,
        "files_failed": run.files_failed,
        "symbols_extracted": run.symbols_extracted,
        "imports_extracted": run.imports_extracted,
        "duration_ms": run.duration_ms,
        "error_summary": run.error_summary,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


def _file_to_row(file: RepositoryFile, workspace_id: str) -> dict:
    return {
        "id": file.file_id,
        "workspace_id": workspace_id,
        "relative_path": file.relative_path.replace("\\", "/"),
        "language": file.language,
        "size_bytes": file.size_bytes,
        "sha256": file.sha256,
        "line_count": file.line_count,
        "is_binary": int(file.is_binary),
        "is_generated": int(file.is_generated),
        "is_ignored": int(file.is_ignored),
        "parser_status": file.parser_status,
        "index_version": file.index_version,
        "parser_version": PARSER_VERSION,
    }


def _symbol_to_row(symbol: Symbol) -> dict:
    return {
        "id": symbol.id,
        "workspace_id": symbol.workspace_id,
        "file_id": _file_id_for_path(symbol.workspace_id, symbol.file_path),
        "file_path": symbol.file_path.replace("\\", "/"),
        "kind": symbol.kind,
        "name": symbol.name,
        "qualified_name": symbol.qualified_name,
        "parent_symbol_id": symbol.parent_symbol_id,
        "start_line": symbol.start_line,
        "end_line": symbol.end_line,
        "start_byte": symbol.start_byte,
        "end_byte": symbol.end_byte,
        "signature": symbol.signature,
        "metadata_json": symbol.metadata,
    }


def _import_to_row(record: ImportRecord) -> dict:
    return {
        "id": record.id,
        "workspace_id": record.workspace_id,
        "file_id": _file_id_for_path(record.workspace_id, record.file_path),
        "file_path": record.file_path.replace("\\", "/"),
        "module_path": record.module_path,
        "imported_name": record.imported_name,
        "alias": record.alias,
        "start_line": record.start_line,
        "resolution_status": record.resolution_status,
        "resolved_path": record.resolved_path,
    }


def _file_id_for_path(workspace_id: str, relative_path: str) -> str:
    import hashlib

    normalized = relative_path.replace("\\", "/")
    return hashlib.sha256(f"{workspace_id}:{normalized}".encode()).hexdigest()
