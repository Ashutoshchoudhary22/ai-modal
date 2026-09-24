"""Configurable diagnostics tool."""

from __future__ import annotations

from typing import Any

from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.tools.base import BaseTool
from agent.tools.terminal import LocalCommandExecutor, parse_command, validate_command_policy
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult


class CodeDiagnosticsTool(BaseTool):
    definition = ToolDefinition(
        name="code.diagnostics",
        description="Run configured project diagnostics commands",
        parameters_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "description": "Diagnostic name or index"},
            },
        },
        permissions=[ToolPermission.EXECUTE],
    )

    def __init__(
        self,
        settings: ToolSettings | None = None,
        executor: LocalCommandExecutor | None = None,
    ) -> None:
        self._settings = settings or load_tool_settings()
        self._executor = executor or LocalCommandExecutor()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        commands = self._settings.diagnostics_commands
        if not commands:
            return self._ok({"results": [], "message": "No diagnostics configured"})
        tool_name = arguments.get("tool")
        selected = commands
        if tool_name is not None:
            if tool_name.isdigit():
                idx = int(tool_name)
                selected = [commands[idx]] if 0 <= idx < len(commands) else []
            else:
                selected = [c for c in commands if c.startswith(tool_name)]
        results = []
        for command in selected:
            try:
                argv = parse_command(command)
                validate_command_policy(
                    argv,
                    allowed=self._settings.terminal_allowed_commands,
                    denied=self._settings.terminal_denied_commands,
                )
            except ValueError as exc:
                results.append(
                    {
                        "tool": command,
                        "command": command,
                        "exit_code": None,
                        "stdout": "",
                        "stderr": str(exc),
                        "duration_ms": 0,
                    }
                )
                continue
            run = self._executor.run(
                argv,
                cwd=str(context.workspace_root),
                timeout_sec=self._settings.terminal_timeout_sec,
                max_output_chars=self._settings.terminal_max_output_chars,
            )
            results.append(
                {
                    "tool": command,
                    "command": command,
                    "exit_code": run.get("exit_code"),
                    "stdout": run.get("stdout", ""),
                    "stderr": run.get("stderr", ""),
                    "duration_ms": run.get("duration_ms"),
                }
            )
        return self._ok({"results": results})
