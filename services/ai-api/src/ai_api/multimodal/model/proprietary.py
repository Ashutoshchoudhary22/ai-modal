"""Proprietary multimodal model placeholder."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ai_platform_protocol.multimodal import (
    MultimodalCapabilities,
    MultimodalRequest,
    MultimodalResponse,
    MultimodalStreamChunk,
)


class ProprietaryMultimodalModel:
    provider_id = "proprietary"

    def __init__(self, model_id: str = "proprietary-multimodal") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def is_available(self) -> bool:
        return False

    def capabilities(self) -> MultimodalCapabilities:
        return MultimodalCapabilities(modalities=["multimodal"])

    async def generate(self, request: MultimodalRequest) -> MultimodalResponse:
        raise NotImplementedError("Proprietary multimodal model is not available in Phase 10")

    async def generate_structured(self, request: MultimodalRequest) -> MultimodalResponse:
        raise NotImplementedError("Proprietary multimodal model is not available in Phase 10")

    async def stream(self, request: MultimodalRequest) -> AsyncIterator[MultimodalStreamChunk]:
        raise NotImplementedError("Proprietary multimodal model is not available in Phase 10")
        yield MultimodalStreamChunk(type="error")  # pragma: no cover

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))
