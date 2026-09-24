"""Evaluation report generation."""

from __future__ import annotations

import json
from pathlib import Path

from training.evaluation.comparison.compare import ComparisonRow
from training.evaluation.metrics.registry import get
from training.evaluation.metrics.scoring import aggregate_rate, median
from training.evaluation.regression.detector import RegressionResult
from training.evaluation.types import EvaluationResult, MetricValue


def aggregate_metrics(sample_results, benchmark_metrics: list[str]) -> list[MetricValue]:
    values_by_metric: dict[str, list[float]] = {metric_id: [] for metric_id in benchmark_metrics}
    latencies: list[float] = []
    errors = 0
    for sample in sample_results:
        if sample.status == "error":
            errors += 1
        if sample.latency_ms is not None:
            latencies.append(sample.latency_ms)
        for metric_id, value in sample.metrics.items():
            values_by_metric.setdefault(metric_id, []).append(value)

    aggregated: list[MetricValue] = []
    total = len(sample_results)
    for metric_id in benchmark_metrics:
        if metric_id == "latency_ms":
            value = median(latencies)
        elif metric_id == "error_rate":
            value = errors / total if total else 0.0
        else:
            value = aggregate_rate(values_by_metric.get(metric_id, []))
        definition = get(metric_id)
        aggregated.append(
            MetricValue(
                metric_id=metric_id,
                metric_version=definition.version,
                value=value,
                sample_count=total,
                direction=definition.direction,
                unavailable=value is None,
            )
        )
    return aggregated


def write_artifacts(result: EvaluationResult, output_dir: Path, reproducibility: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config.json").write_text(
        json.dumps(result.run.config, indent=2),
        encoding="utf-8",
    )
    summary = {
        "run_id": result.run.run_id,
        "benchmark_id": result.run.benchmark_id,
        "benchmark_version": result.run.benchmark_version,
        "model_id": result.run.model_id,
        "model_provider": result.run.model_provider,
        "status": result.run.status,
        "complete": result.run.complete,
        "completed_samples": result.completed_samples,
        "total_samples": result.total_samples,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "metrics.json").write_text(
        json.dumps([m.model_dump(mode="json") for m in result.metrics], indent=2),
        encoding="utf-8",
    )
    with (output_dir / "samples.jsonl").open("w", encoding="utf-8") as handle:
        for sample in result.sample_results:
            handle.write(json.dumps(sample.model_dump(mode="json"), ensure_ascii=False) + "\n")
    (output_dir / "reproducibility.json").write_text(
        json.dumps(reproducibility, indent=2),
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(render_markdown(result), encoding="utf-8")


def render_markdown(result: EvaluationResult) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"**Run ID:** {result.run.run_id}",
        f"**Benchmark:** {result.run.benchmark_id}@{result.run.benchmark_version}",
        f"**Model:** {result.run.model_id} ({result.run.model_provider})",
        f"**Status:** {result.run.status}",
        "",
        "## Samples",
        "",
        f"- Completed: {result.completed_samples}",
        f"- Failed/Error: {result.errors}",
        f"- Total: {result.total_samples}",
        "",
        "## Metrics",
        "",
    ]
    for metric in result.metrics:
        value = (
            "unavailable" if metric.unavailable or metric.value is None else f"{metric.value:.4f}"
        )
        lines.append(f"- `{metric.metric_id}`: {value} (n={metric.sample_count})")
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(
        ["", "## Reproducibility", "", f"- Dataset fingerprint: `{result.run.dataset_fingerprint}`"]
    )
    return "\n".join(lines) + "\n"


def render_comparison_markdown(rows: list[ComparisonRow], model_a: str, model_b: str) -> str:
    lines = [
        "# Evaluation Comparison",
        "",
        f"**Model A:** {model_a}",
        f"**Model B:** {model_b}",
        "",
        "| metric | model_a | model_b | absolute_difference | relative_difference | direction |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.metric_id} | {row.model_a} | {row.model_b} | "
            f"{row.absolute_difference} | {row.relative_difference} | {row.direction} |"
        )
    return "\n".join(lines) + "\n"


def render_regression_markdown(results: list[RegressionResult]) -> str:
    lines = [
        "# Regression Report",
        "",
        "| metric | baseline | candidate | difference | threshold | status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item.metric_id} | {item.baseline} | {item.candidate} | "
            f"{item.difference} | {item.threshold} | {item.status} |"
        )
    return "\n".join(lines) + "\n"
