"""Screenshot-to-code evaluator."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.types import EvaluationSampleResult, GenerationConfig


def evaluate_screenshot_to_code_sample(
    sample: dict[str, Any],
    *,
    adapter: EvaluationModelAdapter,
    generation: GenerationConfig,
    dataset_root: Path,
) -> EvaluationSampleResult:
    sample_id = str(sample.get("id", "unknown"))
    reference_image = dataset_root / sample.get("reference_image", "reference.png")
    try:
        from agent.render.development_mock import DevelopmentMockRenderer
        from agent.visual.comparator import VisualComparator
        from ai_platform_protocol.vision import RenderRequest

        prompt = str(sample.get("prompt", ""))
        gen = adapter.generate(prompt, config=generation, sample=sample)
        renderer = DevelopmentMockRenderer()
        render_result = asyncio.run(
            renderer.render(
                RenderRequest(
                    workspace_id="eval-screenshot",
                    workspace_root=str(dataset_root),
                    route="/",
                )
            )
        )
        render_success = 1.0 if render_result.success else 0.0
        visual_similarity = 0.0
        layout_similarity = 0.0
        if render_result.success and reference_image.exists():
            comparator = VisualComparator()
            comparison = comparator.compare(
                reference_image.read_bytes(),
                render_result.screenshot_bytes or b"",
            )
            visual_similarity = comparison.score
            layout_similarity = comparison.structural_similarity
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=gen.text,
            reference=str(reference_image),
            metrics={
                "render_success": render_success,
                "visual_similarity": visual_similarity,
                "layout_similarity": layout_similarity,
            },
            latency_ms=gen.latency_ms,
            status="completed" if render_success else "failed",
            failure_category=None if render_success else "RENDER_ERROR",
        )
    except Exception as exc:
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=None,
            reference=str(reference_image),
            metrics={"render_success": 0.0, "visual_similarity": 0.0},
            error=str(exc),
            failure_category="RENDER_ERROR",
            status="error",
        )
