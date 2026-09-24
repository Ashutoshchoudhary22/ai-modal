"""Code completion evaluator."""

from __future__ import annotations

import time
from typing import Any

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.metrics.scoring import exact_match, normalized_match
from training.evaluation.types import EvaluationSampleResult, GenerationConfig


def evaluate_completion_sample(
    sample: dict[str, Any],
    *,
    adapter: EvaluationModelAdapter,
    generation: GenerationConfig,
) -> EvaluationSampleResult:
    sample_id = str(sample.get("id", "unknown"))
    started = time.perf_counter()
    prefix = str(sample.get("prefix", ""))
    suffix = str(sample.get("suffix", ""))
    reference = str(sample.get("expected_completion", sample.get("reference", "")))
    language = str(sample.get("language", sample.get("metadata", {}).get("language", "plaintext")))

    try:
        from ai_platform_protocol.completion import (
            CompletionOptions,
            CompletionPosition,
            CompletionRequest,
        )

        request = CompletionRequest(
            file_path=str(sample.get("file_path", "sample.ts")),
            language=language,
            prefix=prefix,
            suffix=suffix,
            cursor=CompletionPosition(line=0, column=len(prefix.split("\n")[-1])),
            options=CompletionOptions(
                max_tokens=generation.max_tokens,
                temperature=generation.temperature,
            ),
        )
        result = adapter.complete(request, config=generation)
        prediction = result.text
        latency = (time.perf_counter() - started) * 1000
        em = exact_match(prediction, reference)
        nm = normalized_match(prediction, reference)
        prefix_ok = 1.0 if not prediction.startswith(prefix) else 0.0
        suffix_ok = 1.0 if not (suffix and prediction.endswith(suffix)) else 0.0
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=prediction,
            reference=reference,
            metrics={
                "exact_match": em,
                "normalized_match": nm,
                "prefix_preservation": prefix_ok,
                "suffix_preservation": suffix_ok,
                "syntax_validity": 1.0 if prediction.strip() else 0.0,
            },
            latency_ms=latency,
            status="completed",
        )
    except Exception as exc:
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=None,
            reference=reference,
            metrics={"exact_match": 0.0, "normalized_match": 0.0},
            error=str(exc),
            failure_category="MODEL_ERROR",
            status="error",
        )
