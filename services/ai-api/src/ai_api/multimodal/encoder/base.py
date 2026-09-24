"""Vision encoder protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_platform_protocol.multimodal import ProcessedImage, VisionEncoderOutput


@runtime_checkable
class VisionEncoder(Protocol):
    @property
    def encoder_id(self) -> str: ...

    def is_available(self) -> bool: ...

    async def encode(self, images: list[ProcessedImage]) -> VisionEncoderOutput: ...
