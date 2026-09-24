"""Terminal execution tools."""

from __future__ import annotations

import shlex
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any

from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode
from agent.security import reject_shell_metacharacters
from agent.tools.base import BaseTool
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult


class CommandExecutor(ABC):
    @abstractmethod
    def run(
        self,
        argv: list[str],
        *,
        cwd: str,
        timeout_sec: int,
        max_output_chars: int,
    ) -> dict[str, Any]:
        raise NotImplementedError


class LocalCommandExecutor(CommandExecutor):
    def run(
        self,
        argv: list[str],
        *,
        cwd: str,
        timeout_sec: int,
        max_output_chars: int,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "")[:max_output_chars] if exc.stdout else ""
            stderr = (exc.stderr or "")[:max_output_chars] if exc.stderr else ""
            return {
                "success": False,
                "exit_code": None,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "error_code": ToolErrorCode.COMMAND_TIMEOUT.value,
            }
        stdout = (result.stdout or "")[:max_output_chars]
        stderr = (result.stderr or "")[:max_output_chars]
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }


def parse_command(command: str) -> list[str]:
    reject_shell_metacharacters(command)
    return shlex.split(command, posix=False)


def validate_command_policy(
    argv: list[str],
    *,
    allowed: list[str],
    denied: list[str],
) -> None:
    if not argv:
        raise ValueError("Empty command")
    executable = argv[0].split("\\")[-1].split("/")[-1].lower()
    if executable.endswith(".exe"):
        executable = executable[:-4]
    if executable in denied:
        raise ValueError(f"Command denied: {executable}")
    if allowed and executable not in allowed:
        raise ValueError(f"Command not in allowlist: {executable}")
    joined = " ".join(argv).lower()
    for pattern in ("-rf /", "-rf \\", "format c:", "remove-item -recurse"):
        if pattern in joined:
            raise ValueError(f"Dangerous argument pattern detected: {pattern}")


class TerminalExecTool(BaseTool):
    definition = ToolDefinition(
        name="terminal.exec",
        description="Execute an allowlisted command in the workspace",
        parameters_schema={
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
        permissions=[ToolPermission.EXECUTE],
        timeout_sec=120,
    )

    def __init__(
        self,
        settings: ToolSettings | None = None,
        executor: CommandExecutor | None = None,
    ) -> None:
        self._settings = settings or load_tool_settings()
        self._executor = executor or LocalCommandExecutor()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        if not self._settings.terminal_enabled:
            return self._fail(ToolErrorCode.TERMINAL_DISABLED, "Terminal execution is disabled")
        self._require_args(arguments, "command")
        command = arguments["command"].strip()
        try:
            argv = parse_command(command)
            validate_command_policy(
                argv,
                allowed=self._settings.terminal_allowed_commands,
                denied=self._settings.terminal_denied_commands,
            )
        except ValueError as exc:
            return self._fail(ToolErrorCode.COMMAND_NOT_ALLOWED, str(exc))
        timeout = min(context.timeout_sec, self._settings.terminal_timeout_sec)
        result = self._executor.run(
            argv,
            cwd=str(context.workspace_root),
            timeout_sec=timeout,
            max_output_chars=self._settings.terminal_max_output_chars,
        )
        if result.get("error_code") == ToolErrorCode.COMMAND_TIMEOUT.value:
            return self._fail(ToolErrorCode.COMMAND_TIMEOUT, "Command timed out")
        if not result["success"]:
            return ToolResult(
                success=False,
                error=result.get("stderr") or "Command failed",
                error_code=ToolErrorCode.COMMAND_FAILED.value,
                metadata=result,
            )
        return self._ok(result)
