import asyncio

from agent.errors import ToolErrorCode
from agent.tools.filesystem import FileEditTool, FileListTool, FileReadTool, FileWriteTool


def test_read_file(tool_context):
    result = asyncio.run(FileReadTool().execute({"path": "src/app.py"}, tool_context))
    assert result.success
    assert "PORT" in result.metadata["content"]


def test_read_line_range(tool_context):
    result = asyncio.run(
        FileReadTool().execute({"path": "src/app.py", "start_line": 1, "end_line": 1}, tool_context)
    )
    assert result.success
    assert result.metadata["start_line"] == 1


def test_read_missing(tool_context):
    result = asyncio.run(FileReadTool().execute({"path": "missing.py"}, tool_context))
    assert result.error_code == ToolErrorCode.FILE_NOT_FOUND.value


def test_sensitive_file_denied(tool_context):
    result = asyncio.run(FileReadTool().execute({"path": ".env"}, tool_context))
    assert result.error_code == ToolErrorCode.SENSITIVE_FILE.value


def test_traversal_denied(tool_context):
    result = asyncio.run(FileReadTool().execute({"path": "../outside.txt"}, tool_context))
    assert result.error_code == ToolErrorCode.PATH_OUTSIDE_WORKSPACE.value


def test_list_files(tool_context):
    result = asyncio.run(FileListTool().execute({"path": "src"}, tool_context))
    assert result.success
    assert any("app.py" in e for e in result.metadata["entries"])


def test_write_and_edit(tool_context):
    write = asyncio.run(
        FileWriteTool().execute({"path": "src/new.py", "content": "x = 1\n"}, tool_context)
    )
    assert write.success
    edit = asyncio.run(
        FileEditTool().execute(
            {"path": "src/app.py", "old_text": "3000", "new_text": "4000"},
            tool_context,
        )
    )
    assert edit.success
    read = asyncio.run(FileReadTool().execute({"path": "src/app.py"}, tool_context))
    assert "4000" in read.metadata["content"]


def test_edit_missing_text(tool_context):
    result = asyncio.run(
        FileEditTool().execute(
            {"path": "src/app.py", "old_text": "NOT_PRESENT", "new_text": "x"},
            tool_context,
        )
    )
    assert result.error_code == ToolErrorCode.EDIT_TARGET_NOT_FOUND.value


def test_edit_ambiguous(tool_context):
    content = "repeat\nrepeat\n"
    asyncio.run(FileWriteTool().execute({"path": "src/dup.py", "content": content}, tool_context))
    result = asyncio.run(
        FileEditTool().execute(
            {"path": "src/dup.py", "old_text": "repeat", "new_text": "once"},
            tool_context,
        )
    )
    assert result.error_code == ToolErrorCode.EDIT_TARGET_AMBIGUOUS.value
