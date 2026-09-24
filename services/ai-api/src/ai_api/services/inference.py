"""Inference service layer."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from ai_api.knowledge.base import KnowledgeRetriever
from ai_api.knowledge.factory import create_knowledge_retriever
from ai_api.services.chat_context import extract_last_user_message, prepare_generate_request
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
from ai_platform_shared.config import Settings, get_settings
from ai_platform_shared.logging import get_logger

logger = get_logger(__name__)


class InferenceService:
    def __init__(
        self,
        provider: ModelProvider,
        settings: Settings | None = None,
        knowledge: KnowledgeRetriever | None = None,
    ) -> None:
        self._provider = provider
        self._settings = settings or get_settings()
        self._knowledge = knowledge or create_knowledge_retriever(self._settings)

    @property
    def provider(self) -> ModelProvider:
        return self._provider

    async def _prepare_request(self, request: GenerateRequest) -> GenerateRequest:
        rag_context: str | None = None
        if self._settings.chat_rag_enabled:
            messages = request.resolved_messages()
            query = extract_last_user_message(messages)
            workspace_id = str(request.metadata.get("workspace_id") or "")
            if query:
                result = await self._knowledge.retrieve(
                    query,
                    workspace_id=workspace_id or None,
                    max_chars=self._settings.chat_rag_max_chars,
                )
                rag_context = result.context_text or None
        return prepare_generate_request(request, self._settings, rag_context=rag_context)

    async def generate(
        self, request: GenerateRequest, *, request_id: str | None = None
    ) -> GenerateResponse:
        correlation_id = request_id or str(uuid.uuid4())
        prepared = await self._prepare_request(request)
        started = time.perf_counter()
        response = await self._provider.generate(prepared)
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
        prepared = await self._prepare_request(request)
        started = time.perf_counter()
        prompt_tokens = self._provider.count_tokens(
            "\n".join(f"{m.role}: {m.content}" for m in prepared.resolved_messages()),
            prepared.model,
        )
        completion_tokens = 0
        async for chunk in self._provider.stream(prepared):
            if chunk.type == "done" and chunk.usage is not None:
                completion_tokens = chunk.usage.completion_tokens
            yield chunk
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._log_inference(
            correlation_id=correlation_id,
            operation="stream",
            model=prepared.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=elapsed_ms,
            streaming=True,
        )

    async def generate_structured(
        self, request: StructuredGenerateRequest, *, request_id: str | None = None
    ) -> StructuredGenerateResponse:
        correlation_id = request_id or str(uuid.uuid4())
        prepared = await self._prepare_request(
            GenerateRequest(
                model=request.model,
                messages=request.messages,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                metadata=request.metadata,
            )
        )
        structured_request = StructuredGenerateRequest(
            model=prepared.model,
            messages=prepared.messages,
            response_schema=request.response_schema,
            max_tokens=prepared.max_tokens,
            temperature=prepared.temperature,
            top_p=prepared.top_p,
            metadata=request.metadata,
        )
        started = time.perf_counter()
        response = await self._provider.generate_structured(structured_request)
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
