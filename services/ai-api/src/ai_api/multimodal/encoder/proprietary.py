"""Proprietary vision encoder placeholder."""

from __future__ import annotations

from ai_platform_protocol.multimodal import ProcessedImage, VisionEncoderOutput


class ProprietaryVisionEncoder:
    encoder_id = "proprietary"

    def is_available(self) -> bool:
        return False

    async def encode(self, images: list[ProcessedImage]) -> VisionEncoderOutput:
        raise NotImplementedError("Proprietary vision encoder is not available in Phase 10")
