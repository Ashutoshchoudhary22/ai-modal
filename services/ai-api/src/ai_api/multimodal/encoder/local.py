"""Local vision encoder — optional dependency boundary."""

from __future__ import annotations

from ai_api.multimodal.errors import MultimodalError
from ai_platform_protocol.multimodal import MultimodalErrorCode, ProcessedImage, VisionEncoderOutput


class LocalVisionEncoder:
    encoder_id = "local"

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False

    async def encode(self, images: list[ProcessedImage]) -> VisionEncoderOutput:
        raise MultimodalError(
            MultimodalErrorCode.VISION_ENCODER_UNAVAILABLE,
            "Local vision encoder is not configured. Use development_mock for tests.",
        )
