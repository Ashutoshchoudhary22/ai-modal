"""Model client for agent decisions."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from ai_platform_protocol.models.inference import (
    ChatMessage,
    GenerateRequest,
    StructuredGenerateRequest,
)

from agent.loop.errors import AgentErrorCode, AgentExecutionError
from agent.loop.prompts import (
    AGENT_SYSTEM_PROMPT,
    DECISION_RESPONSE_SCHEMA,
    build_tool_schema_prompt,
)
from agent.loop.state import AgentState


@runtime_checkable
class DecisionModel(Protocol):
    async def generate_structured(self, request: StructuredGenerateRequest) -> Any: ...

    async def generate(self, request: GenerateRequest) -> Any: ...


class AgentModelClient(ABC):
    @abstractmethod
    async def decide(
        self,
        state: AgentState,
        tools: list[dict[str, Any]],
    ) -> ModelDecision:
        raise NotImplementedError


class StructuredModelClient(AgentModelClient):
    def __init__(self, provider: DecisionModel, model_id: str = "default") -> None:
        self._provider = provider
        self._model_id = model_id

    async def decide(self, state: AgentState, tools: list[dict[str, Any]]) -> ModelDecision:
        messages = self._build_messages(state, tools)
        request = StructuredGenerateRequest(
            model=self._model_id,
            messages=messages,
            response_schema=DECISION_RESPONSE_SCHEMA,
            temperature=0.2,
            max_tokens=2048,
        )
        try:
            response = await self._provider.generate_structured(request)
            return self._parse_parsed(response.parsed)
        except Exception as exc:
            raise AgentExecutionError(
                AgentErrorCode.MODEL_ERROR, f"Model call failed: {exc}"
            ) from exc

    def _build_messages(self, state: AgentState, tools: list[dict[str, Any]]) -> list[ChatMessage]:
        system = AGENT_SYSTEM_PROMPT + "\n\n" + build_tool_schema_prompt(tools)
        messages = [ChatMessage(role="system", content=system)]
        messages.append(ChatMessage(role="user", content=f"Task:\n{state.user_task}"))
        for msg in state.messages:
            messages.append(ChatMessage(role=msg.role, content=msg.content))
        return messages

    @staticmethod
    def _parse_parsed(parsed: dict[str, Any]) -> ModelDecision:
        raw_type = str(parsed.get("type", "")).lower()
        if raw_type == "final":
            message = parsed.get("message")
            if not message:
                raise AgentExecutionError(
                    AgentErrorCode.MODEL_INVALID_RESPONSE, "Final decision missing message"
                )
            return ModelDecision(type=ModelDecisionType.FINAL, message=str(message))
        if raw_type == "tool_call":
            tool_name = parsed.get("tool_name")
            if not tool_name:
                raise AgentExecutionError(
                    AgentErrorCode.MODEL_INVALID_RESPONSE, "Tool call missing tool_name"
                )
            arguments = parsed.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise AgentExecutionError(
                    AgentErrorCode.MODEL_INVALID_RESPONSE, "Tool arguments must be an object"
                )
            return ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name=str(tool_name),
                arguments=arguments,
            )
        raise AgentExecutionError(
            AgentErrorCode.MODEL_INVALID_RESPONSE, f"Unknown decision type: {raw_type}"
        )


class TextJsonModelClient(AgentModelClient):
    """Fallback parser for providers that return JSON in plain text."""

    def __init__(self, provider: DecisionModel, model_id: str = "default") -> None:
        self._provider = provider
        self._model_id = model_id
        self._structured = StructuredModelClient(provider, model_id)

    async def decide(self, state: AgentState, tools: list[dict[str, Any]]) -> ModelDecision:
        if hasattr(self._provider, "generate_structured"):
            return await self._structured.decide(state, tools)
        messages = self._structured._build_messages(state, tools)
        request = GenerateRequest(
            model=self._model_id,
            messages=messages,
            temperature=0.2,
            max_tokens=2048,
        )
        try:
            response = await self._provider.generate(request)
            parsed = _extract_json_object(response.content)
            return StructuredModelClient._parse_parsed(parsed)
        except AgentExecutionError:
            raise
        except Exception as exc:
            raise AgentExecutionError(
                AgentErrorCode.MODEL_ERROR, f"Model call failed: {exc}"
            ) from exc


class ScriptedModelClient(AgentModelClient):
    """Deterministic model for tests."""

    def __init__(self, decisions: list[ModelDecision]) -> None:
        self._decisions = list(decisions)
        self._index = 0
        self.calls: list[AgentState] = []

    async def decide(self, state: AgentState, tools: list[dict[str, Any]]) -> ModelDecision:
        self.calls.append(state)
        if self._index >= len(self._decisions):
            return ModelDecision(
                type=ModelDecisionType.FINAL,
                message="Task completed (scripted model exhausted).",
            )
        decision = self._decisions[self._index]
        self._index += 1
        return decision


def _extract_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AgentExecutionError(
            AgentErrorCode.MODEL_INVALID_RESPONSE, "No JSON object found in model response"
        )
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise AgentExecutionError(
            AgentErrorCode.MODEL_INVALID_RESPONSE, "Model JSON must be an object"
        )
    return parsed
