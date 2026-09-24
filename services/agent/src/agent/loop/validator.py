"""Tool call validation before execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_platform_protocol.agent import ModelDecision, ModelDecisionType

from agent.loop.errors import AgentErrorCode, AgentExecutionError
from agent.loop.limits import AgentLimits, LimitCounters, check_same_tool_limit
from agent.loop.policy import AgentPolicy
from agent.registry import ToolRegistry


@dataclass
class ValidationResult:
    ok: bool
    error_code: AgentErrorCode | None = None
    message: str | None = None


class ToolCallValidator:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def validate(
        self,
        decision: ModelDecision,
        *,
        policy: AgentPolicy,
        counters: LimitCounters,
        limits: AgentLimits,
    ) -> ValidationResult:
        if decision.type != ModelDecisionType.TOOL_CALL:
            return ValidationResult(
                ok=False,
                error_code=AgentErrorCode.MODEL_INVALID_RESPONSE,
                message="Expected tool_call decision",
            )
        tool_name = decision.tool_name or ""
        try:
            policy.assert_tool_allowed(tool_name)
        except AgentExecutionError as exc:
            return ValidationResult(ok=False, error_code=exc.code, message=exc.message)

        same_tool = check_same_tool_limit(counters, tool_name, limits)
        if same_tool:
            return ValidationResult(
                ok=False,
                error_code=same_tool,
                message=f"Same-tool call limit reached for {tool_name}",
            )

        tool = self._registry.get(tool_name)
        if tool is None:
            return ValidationResult(
                ok=False,
                error_code=AgentErrorCode.TOOL_NOT_FOUND,
                message=f"Unknown tool: {tool_name}",
            )

        required = tool.definition.parameters_schema.get("required", [])
        missing = [key for key in required if key not in (decision.arguments or {})]
        if missing:
            return ValidationResult(
                ok=False,
                error_code=AgentErrorCode.INVALID_ARGUMENTS,
                message=f"Missing required arguments: {', '.join(missing)}",
            )
        return ValidationResult(ok=True)

    @staticmethod
    def validate_arguments_schema(
        arguments: dict[str, Any], schema: dict[str, Any]
    ) -> ValidationResult:
        if schema.get("type") != "object":
            return ValidationResult(ok=True)
        required = schema.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            return ValidationResult(
                ok=False,
                error_code=AgentErrorCode.INVALID_ARGUMENTS,
                message=f"Missing required arguments: {', '.join(missing)}",
            )
        return ValidationResult(ok=True)
