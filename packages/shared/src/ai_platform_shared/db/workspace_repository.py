"""Workspace persistence repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform_shared.db.models import OrganizationORM, TeamORM, WorkspaceORM


class WorkspaceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, workspace_id: str) -> WorkspaceORM | None:
        return self._session.get(WorkspaceORM, workspace_id)

    def get_by_root_path(self, root_path: str) -> WorkspaceORM | None:
        normalized = str(root_path).replace("\\", "/")
        return self._session.scalar(
            select(WorkspaceORM).where(WorkspaceORM.root_path == normalized)
        )

    def create(self, *, name: str, root_path: str, team_id: str | None = None) -> WorkspaceORM:
        return self.create_with_id(
            workspace_id=str(uuid.uuid4()),
            name=name,
            root_path=root_path,
            team_id=team_id,
        )

    def create_with_id(
        self,
        *,
        workspace_id: str,
        name: str,
        root_path: str,
        team_id: str | None = None,
    ) -> WorkspaceORM:
        resolved_team_id = team_id or self.ensure_default_team_id()
        normalized = str(root_path).replace("\\", "/")
        row = WorkspaceORM(
            id=workspace_id,
            team_id=resolved_team_id,
            name=name,
            root_path=normalized,
            settings={},
        )
        self._session.add(row)
        self._session.flush()
        return row

    def ensure_default_team_id(self) -> str:
        existing = self._session.scalar(select(TeamORM).limit(1))
        if existing:
            return existing.id
        org = self._session.scalar(select(OrganizationORM).where(OrganizationORM.slug == "dev-org"))
        if org is None:
            org = OrganizationORM(
                id=str(uuid.uuid4()),
                name="Development Org",
                slug="dev-org",
                plan="free",
            )
            self._session.add(org)
            self._session.flush()
        team = TeamORM(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            name="Default Team",
        )
        self._session.add(team)
        self._session.flush()
        return team.id
