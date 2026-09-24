import asyncio

import pytest
from agent.errors import ToolErrorCode, ToolExecutionError
from agent.tools.terminal import (
    LocalCommandExecutor,
    TerminalExecTool,
    parse_command,
    validate_command_policy,
)


def test_allowed_command(tool_context):
    result = asyncio.run(TerminalExecTool().execute({"command": "python --version"}, tool_context))
    assert result.success or result.error_code == ToolErrorCode.COMMAND_FAILED.value


def test_denied_command(tool_context):
    result = asyncio.run(TerminalExecTool().execute({"command": "rm -rf ."}, tool_context))
    assert result.error_code == ToolErrorCode.COMMAND_NOT_ALLOWED.value


def test_shell_metacharacters():
    with pytest.raises(ToolExecutionError):
        parse_command("echo ok; rm -rf /")


def test_command_policy_denied():
    with pytest.raises(ValueError):
        validate_command_policy(["del", "file"], allowed=["python"], denied=["del"])


def test_output_limit(tool_context):
    class LimitExecutor(LocalCommandExecutor):
        def run(self, argv, *, cwd, timeout_sec, max_output_chars):
            return {
                "success": True,
                "exit_code": 0,
                "stdout": "x" * 50,
                "stderr": "",
                "duration_ms": 1,
            }

    result = asyncio.run(
        TerminalExecTool(executor=LimitExecutor()).execute(
            {"command": "python --version"}, tool_context
        )
    )
    assert result.success
