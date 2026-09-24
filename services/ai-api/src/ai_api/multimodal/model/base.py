"""Multimodal model protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from ai_platform_protocol.multimodal import (
    MultimodalCapabilities,
    MultimodalRequest,
    MultimodalResponse,
    MultimodalStreamChunk,
)


@runtime_checkable
class MultimodalModel(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def provider_id(self) -> str: ...

    def is_available(self) -> bool: ...

    def capabilities(self) -> MultimodalCapabilities: ...

    async def generate(self, request: MultimodalRequest) -> MultimodalResponse: ...

    async def generate_structured(self, request: MultimodalRequest) -> MultimodalResponse: ...

    async def stream(self, request: MultimodalRequest) -> AsyncIterator[MultimodalStreamChunk]: ...

    def count_tokens(self, text: str) -> int: ...
