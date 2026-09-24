import asyncio

from agent.tools.code_intel import CodeContextTool, CodeSearchTool, CodeSymbolsTool


def test_code_search(indexed_workspace, tool_context):
    tool_context.workspace_root = indexed_workspace
    result = asyncio.run(CodeSearchTool().execute({"query": "create_connection"}, tool_context))
    assert result.success
    assert result.metadata["matches"]


def test_code_symbols(indexed_workspace, tool_context):
    tool_context.workspace_root = indexed_workspace
    result = asyncio.run(
        CodeSymbolsTool().execute({"symbol_name": "create_connection"}, tool_context)
    )
    assert result.success
    assert result.metadata["symbols"]


def test_code_context(indexed_workspace, tool_context):
    tool_context.workspace_root = indexed_workspace
    result = asyncio.run(CodeContextTool().execute({"query": "connection"}, tool_context))
    assert result.success
    assert result.metadata["snippets"] or result.metadata["files"]
