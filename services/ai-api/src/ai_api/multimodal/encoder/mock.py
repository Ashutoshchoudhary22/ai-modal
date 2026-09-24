"""Deterministic mock vision encoder."""

from __future__ import annotations

import hashlib

from ai_platform_protocol.multimodal import ProcessedImage, VisionEncoderOutput, VisualEmbedding


class DevelopmentMockVisionEncoder:
    encoder_id = "development_mock"
    embedding_dimension = 16

    def is_available(self) -> bool:
        return True

    async def encode(self, images: list[ProcessedImage]) -> VisionEncoderOutput:
        embeddings: list[VisualEmbedding] = []
        total_tokens = 0
        for image in images:
            seed = image.data_reference or image.image_id
            vector = self._deterministic_vector(seed)
            grid_h = max(1, image.metadata.processed_height // 32)
            grid_w = max(1, image.metadata.processed_width // 32)
            token_count = grid_h * grid_w
            total_tokens += token_count
            token_vectors = [vector for _ in range(min(token_count, 4))]
            embeddings.append(
                VisualEmbedding(
                    image_id=image.image_id,
                    embeddings=token_vectors,
                    embedding_dimension=self.embedding_dimension,
                    token_count=token_count,
                    spatial_shape={
                        "grid_height": grid_h,
                        "grid_width": grid_w,
                        "patch_count": token_count,
                    },
                    metadata={"mock": True},
                )
            )
        return VisionEncoderOutput(
            embeddings=embeddings,
            embedding_dimension=self.embedding_dimension,
            token_count=total_tokens,
            metadata={"encoder": self.encoder_id},
        )

    def _deterministic_vector(self, seed: str) -> list[float]:
        digest = hashlib.sha256(seed.encode()).digest()
        return [round(digest[i] / 255.0, 6) for i in range(self.embedding_dimension)]
