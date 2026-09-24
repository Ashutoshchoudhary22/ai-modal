"""ModelProvider protocol — vendor-agnostic inference interface."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from ai_platform_protocol.models.inference import (
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
from ai_platform_protocol.models.provider import ProviderStatus


@runtime_checkable
class ModelProvider(Protocol):
    """Replaceable model provider interface."""

    @property
    def provider_id(self) -> str:
        """Stable provider identifier, e.g. development_mock, local_hf."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...

    async def get_status(self) -> ProviderStatus:
        """Return current provider readiness and diagnostics."""
        ...

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Non-streaming text generation."""
        ...

    async def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        """Async streaming generation."""
        ...

    async def generate_structured(
        self, request: StructuredGenerateRequest
    ) -> StructuredGenerateResponse:
        """JSON/schema constrained generation."""
        ...

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        """Text embeddings."""
        ...

    async def vision(self, request: VisionRequest) -> VisionResponse:
        """Multimodal vision inference (future)."""
        ...

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        """Count tokens using provider-associated tokenizer."""
        ...
