"""Filesystem tools."""

from __future__ import annotations

from typing import Any

from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode, ToolExecutionError
from agent.security import assert_not_sensitive, resolve_tool_path
from agent.tools.base import BaseTool
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult
from code_indexer.binary import is_binary_file
from code_indexer.ignore import IgnoreMatcher


class FileReadTool(BaseTool):
    definition = ToolDefinition(
        name="file.read",
        description="Read a text file from the workspace",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": 1},
            },
            "required": ["path"],
        },
        permissions=[ToolPermission.READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        self._require_args(arguments, "path")
        rel = arguments["path"].replace("\\", "/")
        try:
            assert_not_sensitive(rel)
            path = resolve_tool_path(context.workspace_root, rel)
        except ToolExecutionError as exc:
            return self._fail(exc.code, exc.message)
        if not path.exists():
            return self._fail(ToolErrorCode.FILE_NOT_FOUND, f"File not found: {rel}")
        if path.is_dir():
            return self._fail(ToolErrorCode.INVALID_ARGUMENTS, f"Path is a directory: {rel}")
        if path.stat().st_size > self._settings.max_file_size:
            return self._fail(ToolErrorCode.FILE_TOO_LARGE, f"File exceeds size limit: {rel}")
        if is_binary_file(path):
            return self._fail(ToolErrorCode.FILE_IS_BINARY, f"Binary file cannot be read: {rel}")
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        start = int(arguments.get("start_line", 1))
        end = int(arguments.get("end_line", len(lines) or 1))
        start = max(1, start)
        end = min(len(lines) if lines else 1, end)
        snippet = "\n".join(lines[start - 1 : end])
        if len(snippet) > self._settings.max_output_chars:
            snippet = snippet[: self._settings.max_output_chars]
        return self._ok(
            {
                "path": rel,
                "content": snippet,
                "start_line": start,
                "end_line": end,
            }
        )


class FileListTool(BaseTool):
    definition = ToolDefinition(
        name="file.list",
        description="List files and directories in the workspace",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "recursive": {"type": "boolean", "default": False},
                "include_hidden": {"type": "boolean", "default": False},
            },
        },
        permissions=[ToolPermission.READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        rel = arguments.get("path", ".").replace("\\", "/")
        recursive = bool(arguments.get("recursive", False))
        include_hidden = bool(arguments.get("include_hidden", False))
        try:
            base = resolve_tool_path(context.workspace_root, rel)
        except ToolExecutionError as exc:
            return self._fail(exc.code, exc.message)
        if not base.exists():
            return self._fail(ToolErrorCode.FILE_NOT_FOUND, f"Path not found: {rel}")
        ignore = IgnoreMatcher(context.workspace_root)
        entries: list[str] = []
        if base.is_file():
            entries.append(rel)
        elif recursive:
            for path in sorted(base.rglob("*")):
                if len(entries) >= self._settings.max_list_results:
                    break
                if not include_hidden and any(part.startswith(".") for part in path.parts):
                    continue
                relative = path.relative_to(context.workspace_root).as_posix()
                if ignore.is_ignored(relative):
                    continue
                try:
                    assert_not_sensitive(relative)
                except ToolExecutionError:
                    continue
                suffix = "/" if path.is_dir() else ""
                entries.append(f"{relative}{suffix}")
        else:
            for child in sorted(base.iterdir()):
                if len(entries) >= self._settings.max_list_results:
                    break
                if not include_hidden and child.name.startswith("."):
                    continue
                relative = child.relative_to(context.workspace_root).as_posix()
                if ignore.is_ignored(relative):
                    continue
                try:
                    assert_not_sensitive(relative)
                except ToolExecutionError:
                    continue
                suffix = "/" if child.is_dir() else ""
                entries.append(f"{relative}{suffix}")
        return self._ok({"path": rel, "entries": entries, "count": len(entries)})


class FileWriteTool(BaseTool):
    definition = ToolDefinition(
        name="file.write",
        description="Create or replace a workspace file",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        permissions=[ToolPermission.WRITE],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        if not self._settings.write_enabled:
            return self._fail(ToolErrorCode.WRITE_DISABLED, "File writes are disabled")
        self._require_args(arguments, "path", "content")
        rel = arguments["path"].replace("\\", "/")
        try:
            assert_not_sensitive(rel, write=True)
            path = resolve_tool_path(context.workspace_root, rel)
        except ToolExecutionError as exc:
            return self._fail(exc.code, exc.message)
        content = arguments["content"]
        if len(content.encode("utf-8")) > self._settings.max_file_size:
            return self._fail(ToolErrorCode.FILE_TOO_LARGE, "Content exceeds file size limit")
        if self._settings.create_parent_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        return self._ok({"path": rel, "bytes_written": len(content.encode("utf-8"))})


class FileEditTool(BaseTool):
    definition = ToolDefinition(
        name="file.edit",
        description="Replace exact text in an existing file",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
                "replace_all": {"type": "boolean", "default": False},
            },
            "required": ["path", "old_text", "new_text"],
        },
        permissions=[ToolPermission.WRITE],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        if not self._settings.write_enabled:
            return self._fail(ToolErrorCode.WRITE_DISABLED, "File edits are disabled")
        self._require_args(arguments, "path", "old_text", "new_text")
        rel = arguments["path"].replace("\\", "/")
        try:
            assert_not_sensitive(rel, write=True)
            path = resolve_tool_path(context.workspace_root, rel)
        except ToolExecutionError as exc:
            return self._fail(exc.code, exc.message)
        if not path.exists():
            return self._fail(ToolErrorCode.FILE_NOT_FOUND, f"File not found: {rel}")
        content = path.read_text(encoding="utf-8", errors="replace")
        old_text = arguments["old_text"]
        new_text = arguments["new_text"]
        replace_all = bool(arguments.get("replace_all", False))
        count = content.count(old_text)
        if count == 0:
            return self._fail(ToolErrorCode.EDIT_TARGET_NOT_FOUND, "old_text not found in file")
        if count > 1 and not replace_all:
            return self._fail(
                ToolErrorCode.EDIT_TARGET_AMBIGUOUS,
                f"old_text occurs {count} times; set replace_all=true or provide unique old_text",
            )
        updated = (
            content.replace(old_text, new_text)
            if replace_all
            else content.replace(old_text, new_text, 1)
        )
        replacements = count if replace_all else 1
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(updated, encoding="utf-8")
        tmp.replace(path)
        return self._ok({"path": rel, "replacements": replacements})
