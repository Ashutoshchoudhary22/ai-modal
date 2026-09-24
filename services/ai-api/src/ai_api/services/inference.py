"""Inference service layer."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from ai_platform_protocol.models.inference import (
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
)
from ai_platform_protocol.providers.base import ModelProvider
from ai_platform_shared.logging import get_logger

logger = get_logger(__name__)


class InferenceService:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> ModelProvider:
        return self._provider

    async def generate(
        self, request: GenerateRequest, *, request_id: str | None = None
    ) -> GenerateResponse:
        correlation_id = request_id or str(uuid.uuid4())
        started = time.perf_counter()
        response = await self._provider.generate(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._log_inference(
            correlation_id=correlation_id,
            operation="generate",
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=elapsed_ms,
        )
        return response

    async def stream(
        self, request: GenerateRequest, *, request_id: str | None = None
    ) -> AsyncIterator[StreamChunk]:
        correlation_id = request_id or str(uuid.uuid4())
        started = time.perf_counter()
        prompt_tokens = self._provider.count_tokens(
            "\n".join(f"{m.role}: {m.content}" for m in request.resolved_messages()),
            request.model,
        )
        completion_tokens = 0
        async for chunk in self._provider.stream(request):
            if chunk.type == "done" and chunk.usage is not None:
                completion_tokens = chunk.usage.completion_tokens
            yield chunk
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._log_inference(
            correlation_id=correlation_id,
            operation="stream",
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=elapsed_ms,
            streaming=True,
        )

    async def generate_structured(
        self, request: StructuredGenerateRequest, *, request_id: str | None = None
    ) -> StructuredGenerateResponse:
        correlation_id = request_id or str(uuid.uuid4())
        started = time.perf_counter()
        response = await self._provider.generate_structured(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._log_inference(
            correlation_id=correlation_id,
            operation="structured",
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=elapsed_ms,
        )
        return response

    async def embed(self, request: EmbedRequest, *, request_id: str | None = None) -> EmbedResponse:
        correlation_id = request_id or str(uuid.uuid4())
        started = time.perf_counter()
        response = await self._provider.embed(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._log_inference(
            correlation_id=correlation_id,
            operation="embed",
            model=response.model,
            prompt_tokens=response.usage.total_tokens,
            completion_tokens=0,
            latency_ms=elapsed_ms,
        )
        return response

    def _log_inference(self, **fields: Any) -> None:
        logger.info(
            "inference completed | provider=%s | %s",
            self._provider.provider_id,
            " | ".join(f"{key}={value}" for key, value in fields.items()),
        )
