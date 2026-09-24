"""Model comparison reports."""

from __future__ import annotations

from dataclasses import dataclass

from training.evaluation.metrics.registry import get
from training.evaluation.types import EvaluationResult


@dataclass
class ComparisonRow:
    metric_id: str
    model_a: float | None
    model_b: float | None
    absolute_difference: float | None
    relative_difference: float | None
    sample_count: int
    direction: str


def compare_results(result_a: EvaluationResult, result_b: EvaluationResult) -> list[ComparisonRow]:
    rows: list[ComparisonRow] = []
    b_map = {m.metric_id: m for m in result_b.metrics}
    for metric in result_a.metrics:
        other = b_map.get(metric.metric_id)
        if other is None:
            continue
        diff = None
        rel = None
        if metric.value is not None and other.value is not None:
            diff = other.value - metric.value
            rel = diff / metric.value if metric.value != 0 else None
        definition = get(metric.metric_id, metric.metric_version)
        rows.append(
            ComparisonRow(
                metric_id=metric.metric_id,
                model_a=metric.value,
                model_b=other.value,
                absolute_difference=diff,
                relative_difference=rel,
                sample_count=min(metric.sample_count, other.sample_count),
                direction=definition.direction,
            )
        )
    return rows
