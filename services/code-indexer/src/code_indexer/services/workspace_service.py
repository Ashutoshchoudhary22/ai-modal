"""Workspace creation and lookup service."""

from __future__ import annotations

from pathlib import Path

from ai_platform_shared.db import session_scope
from ai_platform_shared.db.workspace_repository import WorkspaceRepository

from code_indexer.config import IndexerConfig
from code_indexer.models import WorkspaceRecord
from code_indexer.security import (
    PathSecurityError,
    normalize_path_for_storage,
    validate_workspace_root,
)


class WorkspaceService:
    def __init__(self, config: IndexerConfig | None = None) -> None:
        self.config = config or IndexerConfig()

    def create_workspace(
        self,
        *,
        name: str,
        root_path: str,
        team_id: str | None = None,
    ) -> WorkspaceRecord:
        root = validate_workspace_root(
            Path(root_path),
            allowed_roots=self.config.allowed_workspace_roots or None,
        )
        normalized = normalize_path_for_storage(root)
        with session_scope() as session:
            repo = WorkspaceRepository(session)
            existing = repo.get_by_root_path(normalized)
            if existing:
                return WorkspaceRecord(
                    id=existing.id,
                    name=existing.name,
                    root_path=existing.root_path or normalized,
                    team_id=existing.team_id,
                )
            row = repo.create(name=name, root_path=normalized, team_id=team_id)
            return WorkspaceRecord(
                id=row.id,
                name=row.name,
                root_path=row.root_path or normalized,
                team_id=row.team_id,
            )

    def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        with session_scope() as session:
            row = WorkspaceRepository(session).get_by_id(workspace_id)
            if row is None or not row.root_path:
                return None
            return WorkspaceRecord(
                id=row.id,
                name=row.name,
                root_path=row.root_path,
                team_id=row.team_id,
            )

    def _lookup_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        try:
            return self.get_workspace(workspace_id)
        except Exception:
            return None

    def resolve_root_path(self, workspace_id: str, fallback_root: str | None = None) -> Path:
        allowed = self.config.allowed_workspace_roots or None
        record = self._lookup_workspace(workspace_id)
        if record:
            try:
                return validate_workspace_root(Path(record.root_path), allowed_roots=allowed)
            except PathSecurityError:
                if fallback_root:
                    return validate_workspace_root(Path(fallback_root), allowed_roots=allowed)
                raise
        if fallback_root:
            return validate_workspace_root(Path(fallback_root), allowed_roots=allowed)
        raise PathSecurityError(f"Workspace not found: {workspace_id}")
