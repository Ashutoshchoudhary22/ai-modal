"""Tool execution via ToolRegistry."""

from __future__ import annotations

from typing import Any

from ai_platform_protocol.tools import ToolResult

from agent.context import ToolExecutionContext
from agent.registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        return await self._registry.execute(tool_name, arguments, context)
