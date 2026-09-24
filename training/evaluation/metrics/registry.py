"""Metric registry."""

from __future__ import annotations

from training.evaluation.types import MetricDefinition

_METRICS: dict[str, MetricDefinition] = {}


def _register(metric: MetricDefinition) -> None:
    key = f"{metric.metric_id}@{metric.version}"
    _METRICS[key] = metric


def register_defaults() -> None:
    if _METRICS:
        return
    defaults = [
        MetricDefinition(
            metric_id="exact_match",
            name="Exact Match",
            version=1,
            description="Deterministic exact string match",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="normalized_match",
            name="Normalized Match",
            version=1,
            description="Match after configured normalization",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="schema_validity",
            name="Schema Validity",
            version=1,
            description="Structured output schema validity rate",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="field_accuracy",
            name="Field Accuracy",
            version=1,
            description="Structured field-level accuracy",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="code_pass_rate",
            name="Code Pass Rate",
            version=1,
            description="Fraction of coding tests passed",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="visual_similarity",
            name="Visual Similarity",
            version=1,
            description="Visual comparison score",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="layout_similarity",
            name="Layout Similarity",
            version=1,
            description="Layout comparison score",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="render_success",
            name="Render Success",
            version=1,
            description="Whether rendering succeeded",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="task_success",
            name="Task Success",
            version=1,
            description="Agent/browser task completion",
            direction="higher_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="latency_ms",
            name="Latency (ms)",
            version=1,
            description="Median sample latency in milliseconds",
            direction="lower_is_better",
        ),
        MetricDefinition(
            metric_id="error_rate",
            name="Error Rate",
            version=1,
            description="Fraction of samples with errors",
            direction="lower_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
        MetricDefinition(
            metric_id="policy_violation_rate",
            name="Policy Violation Rate",
            version=1,
            description="Rate of policy violations in security cases",
            direction="lower_is_better",
            range_min=0.0,
            range_max=1.0,
        ),
    ]
    for metric in defaults:
        _register(metric)


def get(metric_id: str, version: int = 1) -> MetricDefinition:
    register_defaults()
    key = f"{metric_id}@{version}"
    metric = _METRICS.get(key)
    if metric is None:
        raise KeyError(f"Unknown metric: {metric_id}@{version}")
    return metric


def list_metrics() -> list[MetricDefinition]:
    register_defaults()
    return list(_METRICS.values())
