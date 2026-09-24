"""Deterministic development/test model provider."""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections.abc import AsyncIterator

from ai_platform_protocol.models.common import TokenUsage
from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.models.inference import (
    ChatMessage,
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    VisionRequest,
    VisionResponse,
)
from ai_platform_protocol.models.provider import ProviderCapabilities, ProviderState, ProviderStatus

from ai_api.providers.errors import ProviderError


class _MockTokenizer:
    """Development-only tokenizer approximation for deterministic tests."""

    def encode(self, text: str) -> list[int]:
        if not text:
            return []
        return list(range(len(re.findall(r"\S+", text))))


class DevelopmentMockProvider:
    provider_id = "development_mock"
    provider_name = "Development Mock Provider"

    MOCK_PREFIX = "[development-mock]"

    def __init__(self, default_model: str = "development-mock-v1") -> None:
        self._default_model = default_model
        self._tokenizer = _MockTokenizer()

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            state=ProviderState.READY,
            model_id=self._default_model,
            message="Development/test provider — not for production use",
            capabilities=ProviderCapabilities(
                generate=True,
                stream=True,
                structured=True,
                embed=True,
                vision=False,
                modalities=["text"],
            ),
            diagnostics={"environment": "development_or_test"},
        )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        messages = request.resolved_messages()
        user_content = self._latest_user_content(messages)
        prompt_tokens = self.count_tokens(self._flatten_messages(messages), request.model)
        content = (
            f"{self.MOCK_PREFIX} Received: {user_content[:200]}"
            if user_content
            else f"{self.MOCK_PREFIX} No user message provided."
        )
        completion_tokens = self.count_tokens(content, request.model)
        return GenerateResponse(
            id=f"gen_{uuid.uuid4().hex[:12]}",
            model=request.model if request.model != "default" else self._default_model,
            content=content,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            provider=self.provider_id,
        )

    async def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        messages = request.resolved_messages()
        user_content = self._latest_user_content(messages) or "empty"
        tokens = f"{self.MOCK_PREFIX} stream: {user_content}".split()
        for token in tokens:
            await asyncio.sleep(0)
            yield StreamChunk(type="chunk", content=token + " ", provider=self.provider_id)
        prompt_tokens = self.count_tokens(self._flatten_messages(messages), request.model)
        completion_tokens = len(tokens)
        yield StreamChunk(
            type="done",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            provider=self.provider_id,
        )

    async def generate_structured(
        self, request: StructuredGenerateRequest
    ) -> StructuredGenerateResponse:
        parsed = self._build_structured_payload(request.response_schema)
        prompt_tokens = self.count_tokens(
            self._flatten_messages(request.resolved_messages()), request.model
        )
        return StructuredGenerateResponse(
            id=f"gen_{uuid.uuid4().hex[:12]}",
            model=request.model if request.model != "default" else self._default_model,
            parsed=parsed,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=self.count_tokens(json.dumps(parsed), request.model),
                total_tokens=prompt_tokens + self.count_tokens(json.dumps(parsed), request.model),
            ),
            provider=self.provider_id,
        )

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        if not request.inputs:
            raise ProviderError(
                ProviderErrorCode.INVALID_REQUEST,
                "At least one input is required for embeddings",
            )
        embeddings = [
            [float(idx), float(self.count_tokens(text))] for idx, text in enumerate(request.inputs)
        ]
        total_tokens = sum(self.count_tokens(text) for text in request.inputs)
        return EmbedResponse(
            model=request.model
            if request.model != "embed-default"
            else f"{self._default_model}-embed",
            embeddings=embeddings,
            dimensions=2,
            usage=TokenUsage(total_tokens=total_tokens),
            provider=self.provider_id,
        )

    async def vision(self, request: VisionRequest) -> VisionResponse:
        raise ProviderError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "Vision is not implemented for DevelopmentMockProvider",
            status_code=503,
        )

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        _ = model_id
        return len(self._tokenizer.encode(text))

    @staticmethod
    def _latest_user_content(messages: list[ChatMessage]) -> str:
        for message in reversed(messages):
            if message.role == "user":
                return message.content
        return ""

    @staticmethod
    def _flatten_messages(messages: list[ChatMessage]) -> str:
        return "\n".join(f"{message.role}: {message.content}" for message in messages)

    @staticmethod
    def _build_structured_payload(schema: dict[str, object]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        if schema.get("type") == "object" and isinstance(schema.get("properties"), dict):
            properties = schema["properties"]
            assert isinstance(properties, dict)
            for key, prop in properties.items():
                if isinstance(prop, dict) and prop.get("type") == "array":
                    parsed[key] = ["mock_item_1", "mock_item_2"]
                elif isinstance(prop, dict) and prop.get("type") == "string":
                    parsed[key] = f"mock_{key}"
                else:
                    parsed[key] = None
        return parsed
