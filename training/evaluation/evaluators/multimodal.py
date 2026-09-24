"""Multimodal benchmark evaluator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.metrics.scoring import field_accuracy, normalized_match, schema_validity
from training.evaluation.types import EvaluationSampleResult, GenerationConfig


def evaluate_multimodal_sample(
    sample: dict[str, Any],
    *,
    adapter: EvaluationModelAdapter,
    generation: GenerationConfig,
    dataset_root: Path,
) -> EvaluationSampleResult:
    sample_id = str(sample.get("id", "unknown"))
    reference = sample.get("reference", {})
    try:
        result = adapter.multimodal_generate(sample, config=generation, dataset_root=dataset_root)
        structured = result.structured
        if structured is None:
            try:
                structured = json.loads(result.text)
            except json.JSONDecodeError:
                structured = {}
        ref_dict = reference if isinstance(reference, dict) else {}
        metrics = {
            "schema_validity": schema_validity(structured),
            "field_accuracy": field_accuracy(structured, ref_dict) if ref_dict else 0.0,
            "normalized_match": normalized_match(
                json.dumps(structured, sort_keys=True),
                json.dumps(ref_dict, sort_keys=True),
            ),
        }
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=structured,
            reference=reference,
            metrics=metrics,
            latency_ms=result.latency_ms,
            token_usage={
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
            status="completed",
        )
    except Exception as exc:
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=None,
            reference=reference,
            metrics={"schema_validity": 0.0, "field_accuracy": 0.0},
            error=str(exc),
            failure_category="MODEL_ERROR",
            status="error",
        )
