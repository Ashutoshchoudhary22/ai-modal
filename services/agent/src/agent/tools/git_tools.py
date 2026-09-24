"""Read-only Git tools."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode
from agent.tools.base import BaseTool
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult
from code_indexer.git_info import get_git_metadata


def _git_diff(workspace_root, path: str | None, max_chars: int) -> str:
    args = ["git", "diff"]
    if path:
        args.append(path.replace("\\", "/"))
    result = subprocess.run(
        args,
        cwd=workspace_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode not in (0, 1):
        return ""
    return (result.stdout or "")[:max_chars]


class GitStatusTool(BaseTool):
    definition = ToolDefinition(
        name="git.status",
        description="Read Git repository status",
        parameters_schema={"type": "object", "properties": {}},
        permissions=[ToolPermission.GIT_READ],
    )

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        _ = arguments
        meta = get_git_metadata(context.workspace_root)
        if not meta.is_git_repository:
            return self._fail(ToolErrorCode.GIT_NOT_REPOSITORY, "Not a Git repository")
        lines = []
        if shutil.which("git"):
            proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=context.workspace_root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
        modified = [line[3:] for line in lines if line.startswith((" M", "M ", "MM", "AM"))]
        untracked = [line[3:] for line in lines if line.startswith("??")]
        staged = [line[3:] for line in lines if line and line[0] in "MADRCU" and line[1] != "?"]
        return self._ok(
            {
                "is_git_repository": True,
                "branch": meta.branch,
                "commit": meta.commit,
                "modified_files": modified,
                "untracked_files": untracked,
                "staged_files": staged,
            }
        )


class GitDiffTool(BaseTool):
    definition = ToolDefinition(
        name="git.diff",
        description="Read Git diff (read-only)",
        parameters_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
        permissions=[ToolPermission.GIT_READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        meta = get_git_metadata(context.workspace_root)
        if not meta.is_git_repository:
            return self._fail(ToolErrorCode.GIT_NOT_REPOSITORY, "Not a Git repository")
        path = arguments.get("path")
        diff = _git_diff(context.workspace_root, path, self._settings.max_diff_chars)
        return self._ok(
            {"path": path, "diff": diff, "truncated": len(diff) >= self._settings.max_diff_chars}
        )
