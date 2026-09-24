"""Base tool interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode, ToolExecutionError
from ai_platform_protocol.tools import ToolDefinition, ToolResult


class BaseTool(ABC):
    definition: ToolDefinition

    @abstractmethod
    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        raise NotImplementedError

    def _fail(self, code: ToolErrorCode, message: str) -> ToolResult:
        return ToolResult(success=False, error=message, error_code=code.value)

    def _ok(self, output: dict[str, Any]) -> ToolResult:
        import json

        return ToolResult(
            success=True, output=json.dumps(output, ensure_ascii=False), metadata=output
        )

    def _require_args(self, arguments: dict[str, Any], *keys: str) -> None:
        missing = [key for key in keys if key not in arguments]
        if missing:
            raise ToolExecutionError(
                ToolErrorCode.INVALID_ARGUMENTS,
                f"Missing required arguments: {', '.join(missing)}",
            )
