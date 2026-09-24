"""Coding benchmark evaluator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.metrics.scoring import exact_match
from training.evaluation.sandbox.code_runner import run_code_tests
from training.evaluation.types import EvaluationSampleResult, GenerationConfig, ResourceLimits


def _extract_code(text: str) -> str:
    fence = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text.strip()


def evaluate_coding_sample(
    sample: dict[str, Any],
    *,
    adapter: EvaluationModelAdapter,
    generation: GenerationConfig,
    limits: ResourceLimits,
    tests_dir: Path | None = None,
) -> EvaluationSampleResult:
    sample_id = str(sample.get("id", "unknown"))
    prompt = sample.get("prompt", "")
    reference = sample.get("reference", "")
    try:
        result = adapter.generate(prompt, config=generation, sample=sample)
        code = _extract_code(result.text)
        test_code = sample.get("tests", "")
        if tests_dir and sample.get("tests_file"):
            test_code = (tests_dir / sample["tests_file"]).read_text(encoding="utf-8")
        execution = run_code_tests(code, test_code, timeout_sec=limits.code_timeout_sec)
        metrics = {
            "code_pass_rate": execution.pass_rate,
            "exact_match": exact_match(code, reference) if isinstance(reference, str) else 0.0,
        }
        status = "completed"
        failure = None
        if execution.timed_out:
            failure = "TIMEOUT"
            status = "failed"
        elif not execution.passed:
            failure = "EXECUTION_ERROR"
            status = "failed"
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=code,
            reference=reference,
            metrics=metrics,
            latency_ms=result.latency_ms,
            token_usage={
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
            error=execution.error,
            failure_category=failure,
            status=status,
        )
    except Exception as exc:
        return EvaluationSampleResult(
            sample_id=sample_id,
            prediction=None,
            reference=reference,
            metrics={"code_pass_rate": 0.0},
            error=str(exc),
            failure_category="MODEL_ERROR",
            status="error",
        )
