"""Multimodal fusion protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_platform_protocol.multimodal import VisionEncoderOutput


@runtime_checkable
class MultimodalFusion(Protocol):
    @property
    def fusion_id(self) -> str: ...

    async def fuse(
        self,
        text_inputs: list[str],
        visual_inputs: VisionEncoderOutput,
    ) -> dict[str, Any]: ...
