"""Central tool registry."""

from __future__ import annotations

import time
from typing import Any

from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult

from agent.audit import get_audit_log
from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode, ToolExecutionError
from agent.tools.base import BaseTool
from agent.tools.browser_tools import all_browser_tools
from agent.tools.code_intel import CodeContextTool, CodeSearchTool, CodeSymbolsTool
from agent.tools.diagnostics import CodeDiagnosticsTool
from agent.tools.filesystem import FileEditTool, FileListTool, FileReadTool, FileWriteTool
from agent.tools.git_tools import GitDiffTool, GitStatusTool
from agent.tools.terminal import TerminalExecTool


class ToolRegistry:
    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        for tool in (
            FileReadTool(self._settings),
            FileListTool(self._settings),
            FileWriteTool(self._settings),
            FileEditTool(self._settings),
            CodeSearchTool(self._settings),
            CodeSymbolsTool(self._settings),
            CodeContextTool(self._settings),
            TerminalExecTool(self._settings),
            GitStatusTool(),
            GitDiffTool(self._settings),
            CodeDiagnosticsTool(self._settings),
            *all_browser_tools(),
        ):
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        name = tool.definition.name
        if name in self._tools:
            raise ValueError(f"Duplicate tool registration: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinition]:
        return sorted(
            [tool.definition for tool in self._tools.values()],
            key=lambda d: d.name,
        )

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        if not self._settings.enabled:
            return ToolResult(
                success=False,
                error="Tools are disabled",
                error_code=ToolErrorCode.TOOLS_DISABLED.value,
            )
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {name}",
                error_code=ToolErrorCode.TOOL_NOT_FOUND.value,
            )
        for permission in tool.definition.permissions:
            if not context.has_permission(permission):
                return ToolResult(
                    success=False,
                    error=f"Permission denied: {permission.value}",
                    error_code=ToolErrorCode.PERMISSION_DENIED.value,
                )
        required = tool.definition.parameters_schema.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            return ToolResult(
                success=False,
                error=f"Missing required arguments: {', '.join(missing)}",
                error_code=ToolErrorCode.INVALID_ARGUMENTS.value,
            )
        audit = get_audit_log()
        record = audit.start(
            request_id=context.request_id,
            workspace_id=context.workspace_id,
            tool_name=name,
            actor_id=context.actor_id,
        )
        started = time.perf_counter()
        try:
            result = await tool.execute(arguments, context)
        except ToolExecutionError as exc:
            duration = int((time.perf_counter() - started) * 1000)
            audit.complete(
                record,
                success=False,
                error_type=exc.code.value,
                duration_ms=duration,
            )
            return ToolResult(success=False, error=exc.message, error_code=exc.code.value)
        except Exception as exc:
            duration = int((time.perf_counter() - started) * 1000)
            audit.complete(
                record,
                success=False,
                error_type=ToolErrorCode.TOOL_EXECUTION_FAILED.value,
                duration_ms=duration,
            )
            return ToolResult(
                success=False,
                error=str(exc),
                error_code=ToolErrorCode.TOOL_EXECUTION_FAILED.value,
            )
        duration = int((time.perf_counter() - started) * 1000)
        audit.complete(
            record, success=result.success, error_type=result.error_code, duration_ms=duration
        )
        return result


def default_permissions(settings: ToolSettings | None = None) -> set[ToolPermission]:
    cfg = settings or load_tool_settings()
    return {ToolPermission(p) for p in cfg.default_permissions}
