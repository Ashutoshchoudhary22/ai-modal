"""Future proprietary multimodal vision provider placeholder."""

from __future__ import annotations

from ai_platform_protocol.vision import VisionRequest, VisionResponse


class ProprietaryVisionProvider:
    provider_id = "proprietary"
    provider_name = "Proprietary Vision Provider"

    def is_ready(self) -> bool:
        return False

    async def analyze(self, request: VisionRequest) -> VisionResponse:
        raise NotImplementedError(
            "ProprietaryVisionProvider is not yet available. "
            "This placeholder exists for future multimodal model integration."
        )
