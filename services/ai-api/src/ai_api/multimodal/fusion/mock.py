"""Mock prefix-token fusion strategy."""

from __future__ import annotations

from typing import Any

from ai_platform_protocol.multimodal import VisionEncoderOutput


class DevelopmentMockFusion:
    fusion_id = "prefix_visual_tokens"

    async def fuse(
        self,
        text_inputs: list[str],
        visual_inputs: VisionEncoderOutput,
    ) -> dict[str, Any]:
        visual_tokens = []
        for idx, embedding in enumerate(visual_inputs.embeddings, start=1):
            visual_tokens.append(f"[IMAGE_{idx}]")
            for token_idx, _vector in enumerate(embedding.embeddings, start=1):
                visual_tokens.append(f"[VISUAL_TOKEN_{idx}_{token_idx}]")
        return {
            "strategy": self.fusion_id,
            "text_inputs": text_inputs,
            "visual_tokens": visual_tokens,
            "visual_token_count": visual_inputs.token_count,
            "image_count": len(visual_inputs.embeddings),
        }
