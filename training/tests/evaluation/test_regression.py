from training.evaluation.regression.detector import RegressionRule, classify_regression
from training.evaluation.types import MetricValue


def test_regression_higher_is_better():
    baseline = MetricValue(
        metric_id="code_pass_rate",
        metric_version=1,
        value=0.8,
        sample_count=10,
        direction="higher_is_better",
    )
    candidate = MetricValue(
        metric_id="code_pass_rate",
        metric_version=1,
        value=0.7,
        sample_count=10,
        direction="higher_is_better",
    )
    result = classify_regression(
        baseline, candidate, RegressionRule(metric_id="code_pass_rate", max_drop=0.05)
    )
    assert result.status == "regression"


def test_regression_lower_is_better():
    baseline = MetricValue(
        metric_id="latency_ms",
        metric_version=1,
        value=100.0,
        sample_count=10,
        direction="lower_is_better",
    )
    candidate = MetricValue(
        metric_id="latency_ms",
        metric_version=1,
        value=150.0,
        sample_count=10,
        direction="lower_is_better",
    )
    result = classify_regression(
        baseline,
        candidate,
        RegressionRule(metric_id="latency_ms", max_increase=0.2),
    )
    assert result.status == "regression"
