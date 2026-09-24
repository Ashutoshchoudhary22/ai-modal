"""Evaluation runner."""

from __future__ import annotations

import platform
import sys
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from training.evaluation.adapters.factory import build_adapter
from training.evaluation.benchmarks.registry import get as get_benchmark
from training.evaluation.benchmarks.registry import register_builtin_benchmarks, validate_benchmark
from training.evaluation.config import EvaluationConfig
from training.evaluation.contamination import check_contamination
from training.evaluation.datasets import fingerprint_benchmark_dataset, load_benchmark_samples
from training.evaluation.errors import EvaluationError, EvaluationErrorCode
from training.evaluation.evaluators import (
    evaluate_agent_sample,
    evaluate_browser_sample,
    evaluate_coding_sample,
    evaluate_multimodal_sample,
    evaluate_screenshot_to_code_sample,
)
from training.evaluation.reports.generator import aggregate_metrics, write_artifacts
from training.evaluation.types import EvaluationResult, EvaluationRun


def _validate_capabilities(benchmark, adapter) -> None:
    caps = adapter.capabilities()
    required = set(benchmark.required_capabilities)
    available = {
        "generate": "text" in caps.modalities,
        "complete": "text" in caps.modalities,
        "multimodal_generate": caps.supports_multimodal,
        "agent_execute": caps.supports_agent,
        "browser_execute": caps.supports_browser,
        "render": caps.supports_render,
    }
    missing = [name for name in required if not available.get(name, False)]
    if missing:
        raise EvaluationError(
            EvaluationErrorCode.BENCHMARK_CAPABILITY_UNSUPPORTED,
            f"Model lacks capabilities: {', '.join(missing)}",
            details={"missing": missing},
        )


def build_evaluation_plan(
    benchmark,
    config: EvaluationConfig,
    *,
    sample_count: int,
    adapter,
) -> str:
    caps = adapter.capabilities()
    return (
        "Evaluation Plan\n"
        f"Benchmark: {benchmark.benchmark_id}@{benchmark.version}\n"
        f"Dataset: {benchmark.dataset_id}@{benchmark.dataset_version}\n"
        f"Samples: {sample_count}\n\n"
        f"Model: {config.model_id}\n"
        f"Provider: {config.model_provider}\n"
        f"Checkpoint: {config.model_checkpoint or 'none'}\n"
        f"Capabilities: {', '.join(caps.modalities)}\n\n"
        f"Generation:\n"
        f"  Temperature: {config.generation.temperature}\n"
        f"  Max tokens: {config.generation.max_tokens}\n"
        f"  Seed: {config.seed}\n\n"
        f"Metrics: {', '.join(benchmark.metrics)}\n\n"
        f"Resource limits:\n"
        f"  max_samples: {config.resources.max_samples}\n"
        f"  max_runtime_sec: {config.resources.max_runtime_sec}\n"
    )


def run_evaluation(
    config: EvaluationConfig,
    *,
    benchmark_version: str = "1.0.0",
    dry_run: bool = False,
    cancelled: Callable[[], bool] | None = None,
) -> EvaluationResult:
    register_builtin_benchmarks()
    benchmark = get_benchmark(config.benchmark_id, benchmark_version)
    issues = validate_benchmark(benchmark)
    if issues:
        raise EvaluationError(
            EvaluationErrorCode.BENCHMARK_INVALID,
            "; ".join(issues),
        )

    adapter = build_adapter(config.model_provider, config.model_id, config.model_checkpoint)
    _validate_capabilities(benchmark, adapter)

    dataset_path = Path(benchmark.dataset_path)
    samples = load_benchmark_samples(dataset_path)
    if config.resources.max_samples is not None:
        samples = samples[: config.resources.max_samples]
    if benchmark.max_samples is not None:
        samples = samples[: benchmark.max_samples]

    dataset_fingerprint = fingerprint_benchmark_dataset(samples)
    warnings = check_contamination(config.training_dataset_fingerprint, dataset_fingerprint)

    run = EvaluationRun(
        run_id=str(uuid.uuid4()),
        benchmark_id=benchmark.benchmark_id,
        benchmark_version=benchmark.version,
        model_id=config.model_id,
        model_provider=config.model_provider,
        model_checkpoint=config.model_checkpoint,
        dataset_fingerprint=dataset_fingerprint,
        config=config.model_dump(mode="json"),
        status="validating",
        seed=config.seed,
    )
    output_dir = Path(config.output_dir) / "runs" / run.run_id
    plan = build_evaluation_plan(benchmark, config, sample_count=len(samples), adapter=adapter)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation_plan.txt").write_text(plan, encoding="utf-8")
    print(plan)

    if dry_run:
        run.status = "completed"
        return EvaluationResult(
            run=run,
            metrics=[],
            sample_results=[],
            total_samples=len(samples),
            warnings=warnings,
        )

    run.status = "running"
    started = time.perf_counter()
    sample_results = []
    for sample in samples:
        if cancelled and cancelled():
            run.status = "cancelled"
            run.complete = False
            break
        if (
            config.resources.max_runtime_sec
            and (time.perf_counter() - started) > config.resources.max_runtime_sec
        ):
            run.status = "cancelled"
            run.complete = False
            warnings.append("Evaluation stopped due to max_runtime_sec")
            break

        evaluator = benchmark.evaluator
        if evaluator in {"coding", "debugging"}:
            result = evaluate_coding_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
                limits=config.resources,
                tests_dir=dataset_path,
            )
        elif evaluator == "multimodal":
            result = evaluate_multimodal_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
                dataset_root=dataset_path,
            )
        elif evaluator == "screenshot_to_code":
            result = evaluate_screenshot_to_code_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
                dataset_root=dataset_path,
            )
        elif evaluator == "agent":
            result = evaluate_agent_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
            )
        elif evaluator == "browser":
            result = evaluate_browser_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
            )
        elif evaluator == "completion":
            from training.evaluation.evaluators.completion import evaluate_completion_sample

            result = evaluate_completion_sample(
                sample,
                adapter=adapter,
                generation=config.generation,
            )
        else:
            raise EvaluationError(
                EvaluationErrorCode.BENCHMARK_INVALID,
                f"Unknown evaluator: {evaluator}",
            )
        sample_results.append(result)

    metrics = aggregate_metrics(sample_results, benchmark.metrics)
    errors = sum(1 for sample in sample_results if sample.status == "error")
    completed = sum(1 for sample in sample_results if sample.status == "completed")
    run.status = "completed_with_errors" if errors else "completed"
    run.complete = len(sample_results) == len(samples) and run.status != "cancelled"
    run.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    evaluation_result = EvaluationResult(
        run=run,
        metrics=metrics,
        sample_results=sample_results,
        errors=errors,
        completed_samples=completed,
        total_samples=len(samples),
        warnings=warnings,
    )

    reproducibility = {
        "run_id": run.run_id,
        "model": {
            "id": config.model_id,
            "provider": config.model_provider,
            "checkpoint": config.model_checkpoint,
        },
        "benchmark": {
            "id": benchmark.benchmark_id,
            "version": benchmark.version,
        },
        "dataset": {
            "id": benchmark.dataset_id,
            "version": benchmark.dataset_version,
            "fingerprint": dataset_fingerprint,
        },
        "metric_versions": {metric.metric_id: metric.metric_version for metric in metrics},
        "generation_config": config.generation.model_dump(mode="json"),
        "seed": config.seed,
        "software_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "timestamp": run.completed_at,
    }
    write_artifacts(evaluation_result, output_dir, reproducibility)
    return evaluation_result
