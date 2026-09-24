"""Multimodal inference service."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator

from ai_api.multimodal.errors import MultimodalError
from ai_api.multimodal.factory import create_multimodal_model
from ai_api.multimodal.model.base import MultimodalModel
from ai_api.multimodal.validator import validate_request
from ai_platform_protocol.multimodal import (
    MultimodalBatchRequest,
    MultimodalBatchResponse,
    MultimodalErrorCode,
    MultimodalRequest,
    MultimodalResponse,
    MultimodalStreamChunk,
)
from ai_platform_shared.config import Settings, get_settings
from ai_platform_shared.logging import get_logger

logger = get_logger(__name__)


class MultimodalService:
    def __init__(
        self, model: MultimodalModel | None = None, settings: Settings | None = None
    ) -> None:
        self._settings = settings or get_settings()
        self._model = model or create_multimodal_model(self._settings)

    @property
    def model(self) -> MultimodalModel:
        return self._model

    async def generate(
        self, request: MultimodalRequest, *, request_id: str | None = None
    ) -> MultimodalResponse:
        self._ensure_ready()
        validate_request(
            request,
            self._model.capabilities(),
            max_context_tokens=self._settings.multimodal_max_context_tokens,
            max_images=self._settings.multimodal_max_images,
            max_pixels=self._settings.multimodal_max_pixels,
            max_batch_size=self._settings.multimodal_max_batch_size,
        )
        correlation_id = request_id or str(uuid.uuid4())
        started = time.perf_counter()
        if request.response_schema:
            response = await self._model.generate_structured(request)
        else:
            response = await self._model.generate(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "multimodal inference | provider=%s | request_id=%s | images=%s | latency_ms=%s",
            self._model.provider_id,
            correlation_id,
            response.usage.image_count,
            elapsed_ms,
        )
        return response

    async def stream(
        self, request: MultimodalRequest, *, request_id: str | None = None
    ) -> AsyncIterator[MultimodalStreamChunk]:
        self._ensure_ready()
        request = request.model_copy(update={"stream": True})
        validate_request(
            request,
            self._model.capabilities(),
            max_context_tokens=self._settings.multimodal_max_context_tokens,
            max_images=self._settings.multimodal_max_images,
            max_pixels=self._settings.multimodal_max_pixels,
            max_batch_size=self._settings.multimodal_max_batch_size,
        )
        async for chunk in self._model.stream(request):
            yield chunk

    async def generate_batch(self, batch: MultimodalBatchRequest) -> MultimodalBatchResponse:
        if len(batch.requests) > self._settings.multimodal_max_batch_size:
            raise MultimodalError(
                MultimodalErrorCode.MULTIMODAL_IMAGE_LIMIT_EXCEEDED,
                "Batch size exceeded",
            )
        responses = [await self.generate(request) for request in batch.requests]
        return MultimodalBatchResponse(responses=responses)

    def _ensure_ready(self) -> None:
        if not self._model.is_available():
            raise MultimodalError(
                MultimodalErrorCode.MULTIMODAL_PROVIDER_UNAVAILABLE,
                f"Multimodal model '{self._model.provider_id}' is unavailable",
            )
