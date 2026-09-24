"""Workspace path security."""

from __future__ import annotations

from pathlib import Path


class PathSecurityError(ValueError):
    pass


def resolve_workspace_path(workspace_root: str | Path) -> Path:
    root = Path(workspace_root).resolve()
    if not root.exists():
        raise PathSecurityError(f"Workspace does not exist: {root}")
    if not root.is_dir():
        raise PathSecurityError(f"Workspace is not a directory: {root}")
    return root


def resolve_relative_path(workspace_root: Path, relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise PathSecurityError(f"Path traversal rejected: {relative_path}")
    candidate = (workspace_root / normalized).resolve()
    if workspace_root not in candidate.parents and candidate != workspace_root:
        raise PathSecurityError(f"Path escapes workspace: {relative_path}")
    return candidate


def is_within_workspace(workspace_root: Path, path: Path) -> bool:
    try:
        resolved = path.resolve()
        root = workspace_root.resolve()
        return root in resolved.parents or resolved == root
    except OSError:
        return False


def safe_relative_path(workspace_root: Path, path: Path) -> str:
    resolved = path.resolve()
    if not is_within_workspace(workspace_root, resolved):
        raise PathSecurityError(f"Path escapes workspace: {path}")
    return resolved.relative_to(workspace_root.resolve()).as_posix()
