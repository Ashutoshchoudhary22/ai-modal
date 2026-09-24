"""Mock multimodal projector."""

from __future__ import annotations

from ai_platform_protocol.multimodal import VisionEncoderOutput


class DevelopmentMockProjector:
    projector_id = "development_mock"
    target_dimension = 16

    async def project(self, vision_output: VisionEncoderOutput) -> VisionEncoderOutput:
        projected = []
        for embedding in vision_output.embeddings:
            projected_vectors = []
            for vector in embedding.embeddings:
                projected_vectors.append(vector[: self.target_dimension])
            projected.append(
                embedding.model_copy(
                    update={
                        "embeddings": projected_vectors,
                        "embedding_dimension": self.target_dimension,
                    }
                )
            )
        return vision_output.model_copy(
            update={
                "embeddings": projected,
                "embedding_dimension": self.target_dimension,
                "metadata": {**vision_output.metadata, "projector": self.projector_id},
            }
        )
