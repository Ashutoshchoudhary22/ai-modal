import pytest
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode
from agent.registry import ToolRegistry
from agent.tools.base import BaseTool
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult


class EchoTool(BaseTool):
    definition = ToolDefinition(
        name="test.echo",
        description="echo",
        parameters_schema={
            "type": "object",
            "required": ["msg"],
            "properties": {"msg": {"type": "string"}},
        },
        permissions=[ToolPermission.READ],
    )

    async def execute(self, arguments, context) -> ToolResult:
        return self._ok({"msg": arguments["msg"]})


def test_register_list_execute(registry: ToolRegistry, tool_context: ToolExecutionContext):
    names = {t.name for t in registry.list()}
    assert "file.read" in names
    assert "code.search" in names


def test_unknown_tool(registry: ToolRegistry, tool_context: ToolExecutionContext):
    import asyncio

    result = asyncio.run(registry.execute("missing.tool", {}, tool_context))
    assert result.error_code == ToolErrorCode.TOOL_NOT_FOUND.value


def test_duplicate_registration(tool_settings):
    reg = ToolRegistry(tool_settings)
    reg.register(EchoTool())
    with pytest.raises(ValueError):
        reg.register(EchoTool())


def test_permission_denial(tool_settings, workspace):
    reg = ToolRegistry(tool_settings)
    ctx = ToolExecutionContext(
        workspace_id="x",
        workspace_root=workspace,
        request_id="r",
        permissions=set(),
    )
    import asyncio

    result = asyncio.run(reg.execute("file.read", {"path": "README.md"}, ctx))
    assert result.error_code == ToolErrorCode.PERMISSION_DENIED.value
