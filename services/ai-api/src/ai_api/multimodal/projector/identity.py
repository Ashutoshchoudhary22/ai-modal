"""Identity projector — passes vision embeddings through unchanged."""

from __future__ import annotations

from ai_platform_protocol.multimodal import VisionEncoderOutput


class IdentityProjector:
    projector_id = "identity"

    async def project(self, vision_output: VisionEncoderOutput) -> VisionEncoderOutput:
        return vision_output
