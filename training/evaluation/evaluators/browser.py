"""Browser agent benchmark evaluator."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.types import EvaluationSampleResult, GenerationConfig


def evaluate_browser_sample(
    sample: dict[str, Any],
    *,
    adapter: EvaluationModelAdapter,
    generation: GenerationConfig,
) -> EvaluationSampleResult:
    sample_id = str(sample.get("id", "unknown"))
    metadata = sample.get("metadata") or {}
    with tempfile.TemporaryDirectory(prefix="eval-browser-") as tmp:
        workspace = Path(tmp)
        try:
            result = adapter.browser_execute(sample, config=generation, workspace=workspace)
            structured = result.structured or {}
            task_success = 1.0 if structured.get("task_success") else 0.0
            return EvaluationSampleResult(
                sample_id=sample_id,
                prediction=result.text,
                reference=metadata.get("expected_status", "completed"),
                metrics={"task_success": task_success},
                latency_ms=result.latency_ms,
                status="completed" if task_success else "failed",
            )
        except Exception as exc:
            return EvaluationSampleResult(
                sample_id=sample_id,
                prediction=None,
                reference=metadata.get("expected_status"),
                metrics={"task_success": 0.0},
                error=str(exc),
                failure_category="BROWSER_ERROR",
                status="error",
            )
