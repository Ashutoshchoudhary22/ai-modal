"""Local multimodal model — explicit unavailable boundary."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ai_api.multimodal.errors import MultimodalError
from ai_platform_protocol.multimodal import (
    MultimodalCapabilities,
    MultimodalErrorCode,
    MultimodalRequest,
    MultimodalResponse,
    MultimodalStreamChunk,
)


class LocalMultimodalModel:
    provider_id = "local"

    def __init__(self, model_id: str = "local-multimodal") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False

    def capabilities(self) -> MultimodalCapabilities:
        return MultimodalCapabilities(
            supports_text=True,
            supports_image=True,
            supports_multi_image=False,
            supports_streaming=False,
            supports_structured_output=True,
            modalities=["text", "image", "multimodal"],
        )

    async def generate(self, request: MultimodalRequest) -> MultimodalResponse:
        raise self._unavailable()

    async def generate_structured(self, request: MultimodalRequest) -> MultimodalResponse:
        raise self._unavailable()

    async def stream(self, request: MultimodalRequest) -> AsyncIterator[MultimodalStreamChunk]:
        raise self._unavailable()
        yield MultimodalStreamChunk(type="error", content="unavailable")  # pragma: no cover

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))

    def _unavailable(self) -> MultimodalError:
        return MultimodalError(
            MultimodalErrorCode.MULTIMODAL_PROVIDER_UNAVAILABLE,
            "Local multimodal model is not configured",
        )
