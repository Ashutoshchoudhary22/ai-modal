"""Vision provider protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_platform_protocol.vision import VisionRequest, VisionResponse


@runtime_checkable
class VisionProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    async def analyze(self, request: VisionRequest) -> VisionResponse: ...

    def is_ready(self) -> bool: ...
