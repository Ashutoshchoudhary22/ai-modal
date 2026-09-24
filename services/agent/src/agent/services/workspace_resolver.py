"""Resolve workspace for tool execution."""

from __future__ import annotations

import uuid
from pathlib import Path

from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode, ToolExecutionError
from agent.registry import default_permissions
from code_indexer.security import PathSecurityError
from code_indexer.services.workspace_service import WorkspaceService


def build_context(
    *,
    workspace_id: str,
    root_path: str | None = None,
    request_id: str | None = None,
    actor_id: str | None = None,
    timeout_sec: int = 120,
) -> ToolExecutionContext:
    service = WorkspaceService()
    try:
        root = service.resolve_root_path(workspace_id, fallback_root=root_path)
    except PathSecurityError as exc:
        raise ToolExecutionError(ToolErrorCode.WORKSPACE_NOT_FOUND, str(exc)) from exc
    return ToolExecutionContext(
        workspace_id=workspace_id,
        workspace_root=root,
        request_id=request_id or str(uuid.uuid4()),
        actor_id=actor_id,
        permissions=default_permissions(),
        timeout_sec=timeout_sec,
    )


def build_context_for_path(
    workspace_root: Path, workspace_id: str | None = None
) -> ToolExecutionContext:
    root = workspace_root.resolve()
    return ToolExecutionContext(
        workspace_id=workspace_id or str(uuid.uuid5(uuid.NAMESPACE_URL, str(root))),
        workspace_root=root,
        request_id=str(uuid.uuid4()),
        permissions=default_permissions(),
    )
