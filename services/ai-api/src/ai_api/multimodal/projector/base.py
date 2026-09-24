"""Multimodal projector protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_platform_protocol.multimodal import VisionEncoderOutput


@runtime_checkable
class MultimodalProjector(Protocol):
    @property
    def projector_id(self) -> str: ...

    async def project(self, vision_output: VisionEncoderOutput) -> VisionEncoderOutput: ...
