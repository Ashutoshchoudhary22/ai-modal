"""Regression detection."""

from __future__ import annotations

from dataclasses import dataclass

from training.evaluation.metrics.registry import get
from training.evaluation.types import MetricValue


@dataclass
class RegressionRule:
    metric_id: str
    max_drop: float | None = None
    max_increase: float | None = None


@dataclass
class RegressionResult:
    metric_id: str
    baseline: float | None
    candidate: float | None
    difference: float | None
    relative_difference: float | None
    threshold: float | None
    status: str


def classify_regression(
    baseline: MetricValue,
    candidate: MetricValue,
    rule: RegressionRule,
) -> RegressionResult:
    metric = get(baseline.metric_id, baseline.metric_version)
    if baseline.value is None or candidate.value is None:
        return RegressionResult(
            metric_id=baseline.metric_id,
            baseline=baseline.value,
            candidate=candidate.value,
            difference=None,
            relative_difference=None,
            threshold=None,
            status="insufficient_data",
        )
    diff = candidate.value - baseline.value
    rel = diff / baseline.value if baseline.value != 0 else None
    threshold = rule.max_drop if metric.direction == "higher_is_better" else rule.max_increase
    status = "within_threshold"
    if metric.direction == "higher_is_better":
        if rule.max_drop is not None and diff < -rule.max_drop:
            status = "regression"
        elif diff > 0:
            status = "improvement"
    else:
        if rule.max_increase is not None and diff > rule.max_increase:
            status = "regression"
        elif diff < 0:
            status = "improvement"
    return RegressionResult(
        metric_id=baseline.metric_id,
        baseline=baseline.value,
        candidate=candidate.value,
        difference=diff,
        relative_difference=rel,
        threshold=threshold,
        status=status,
    )
