"""Multimodal structured model client for agent decisions."""

from __future__ import annotations

from typing import Any

from agent.loop.errors import AgentErrorCode, AgentExecutionError
from agent.loop.model_client import StructuredModelClient
from agent.loop.prompts import (
    AGENT_SYSTEM_PROMPT,
    DECISION_RESPONSE_SCHEMA,
    build_tool_schema_prompt,
)
from agent.loop.state import AgentState
from ai_platform_protocol.agent import ModelDecision
from ai_platform_protocol.multimodal import (
    ImageContent,
    MultimodalMessage,
    MultimodalRequest,
    TextContent,
)


class MultimodalStructuredModelClient(StructuredModelClient):
    """Extends StructuredModelClient with optional image context."""

    def __init__(
        self,
        provider: Any,
        model_id: str = "default",
        *,
        image_contents: list[ImageContent] | None = None,
    ) -> None:
        super().__init__(provider, model_id=model_id)
        self._image_contents = image_contents or []

    async def decide(self, state: AgentState, tools: list[dict[str, Any]]) -> ModelDecision:
        if not self._image_contents:
            return await super().decide(state, tools)

        system = AGENT_SYSTEM_PROMPT + "\n\n" + build_tool_schema_prompt(tools)
        content: list = [TextContent(text=f"Task:\n{state.user_task}")]
        for msg in state.messages:
            content.append(TextContent(text=f"{msg.role}: {msg.content}"))
        content.extend(self._image_contents)

        request = MultimodalRequest(
            model=self._model_id,
            messages=[
                MultimodalMessage(role="system", content=[TextContent(text=system)]),
                MultimodalMessage(role="user", content=content),
            ],
            response_schema=DECISION_RESPONSE_SCHEMA,
            temperature=0.2,
            max_tokens=2048,
            metadata={"decision_schema": True},
        )
        try:
            response = await self._provider.generate_structured(request)
            return self._parse_parsed(response.parsed)
        except Exception as exc:
            raise AgentExecutionError(
                AgentErrorCode.MODEL_ERROR, f"Multimodal model call failed: {exc}"
            ) from exc
