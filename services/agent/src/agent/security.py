"""Tool security helpers."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from code_indexer.config import SENSITIVE_PATTERNS
from code_indexer.security import PathSecurityError, resolve_relative_path

from agent.errors import ToolErrorCode, ToolExecutionError


def resolve_tool_path(workspace_root: Path, relative_path: str) -> Path:
    try:
        return resolve_relative_path(workspace_root, relative_path)
    except PathSecurityError as exc:
        raise ToolExecutionError(ToolErrorCode.PATH_OUTSIDE_WORKSPACE, str(exc)) from exc


def assert_not_sensitive(relative_path: str, *, write: bool = False) -> None:
    normalized = relative_path.replace("\\", "/")
    basename = Path(normalized).name
    if normalized.endswith(".env.example"):
        return
    for pattern in SENSITIVE_PATTERNS:
        if pattern.endswith("."):
            if basename.startswith(pattern):
                raise ToolExecutionError(
                    ToolErrorCode.SENSITIVE_FILE,
                    f"Access to sensitive file denied: {relative_path}",
                )
        elif fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(normalized, pattern):
            raise ToolExecutionError(
                ToolErrorCode.SENSITIVE_FILE,
                f"Access to sensitive file denied: {relative_path}",
            )
    if write and basename == ".env":
        raise ToolExecutionError(
            ToolErrorCode.SENSITIVE_FILE,
            f"Writing sensitive file denied: {relative_path}",
        )


def reject_shell_metacharacters(command: str) -> None:
    forbidden = [";", "|", "&&", "||", ">", "<", "`", "$(", "${"]
    for token in forbidden:
        if token in command:
            raise ToolExecutionError(
                ToolErrorCode.COMMAND_NOT_ALLOWED,
                f"Shell metacharacters are not allowed: {token}",
            )
