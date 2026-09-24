"""End-to-end tool workflow on fixture workspace."""

import asyncio

from agent.tools.code_intel import CodeSearchTool
from agent.tools.filesystem import FileEditTool, FileReadTool
from agent.tools.terminal import TerminalExecTool


def test_tool_workflow(indexed_workspace, tool_context):
    tool_context.workspace_root = indexed_workspace

    search = asyncio.run(CodeSearchTool().execute({"query": "create_connection"}, tool_context))
    assert search.success

    read = asyncio.run(FileReadTool().execute({"path": "src/app.py"}, tool_context))
    assert read.success

    edit = asyncio.run(
        FileEditTool().execute(
            {"path": "src/app.py", "old_text": "3000", "new_text": "4000"},
            tool_context,
        )
    )
    assert edit.success

    read2 = asyncio.run(FileReadTool().execute({"path": "src/app.py"}, tool_context))
    assert "4000" in read2.metadata["content"]

    term = asyncio.run(TerminalExecTool().execute({"command": "python --version"}, tool_context))
    assert term.success or term.error_code == "COMMAND_FAILED"
