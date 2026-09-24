import asyncio

import pytest
from agent.errors import ToolErrorCode, ToolExecutionError
from agent.security import reject_shell_metacharacters
from agent.tools.filesystem import FileReadTool
from agent.tools.terminal import parse_command


def test_reject_shell_injection():
    with pytest.raises(ToolExecutionError):
        reject_shell_metacharacters("echo a && del file")


def test_absolute_path_attack(tool_context):
    result = asyncio.run(
        FileReadTool().execute({"path": "C:/Windows/System32/config.sys"}, tool_context)
    )
    assert result.error_code in {
        ToolErrorCode.PATH_OUTSIDE_WORKSPACE.value,
        ToolErrorCode.FILE_NOT_FOUND.value,
    }


def test_parse_command_rejects_chain():
    with pytest.raises(ToolExecutionError):
        parse_command("pytest; rm -rf /")
