from pathlib import Path

from training.evaluation.config import EvaluationConfig
from training.evaluation.runners.runner import run_evaluation


def test_dry_run_coding_mini():
    config = EvaluationConfig(
        benchmark_id="coding-mini",
        model_id="development-mock-v1",
        model_provider="development_mock",
        output_dir="training/output/evaluation-test",
    )
    result = run_evaluation(config, dry_run=True)
    assert result.run.benchmark_id == "coding-mini"
    assert result.total_samples >= 1


def test_run_coding_mini(tmp_path: Path):
    config = EvaluationConfig(
        benchmark_id="coding-mini",
        model_id="development-mock-v1",
        model_provider="development_mock",
        output_dir=str(tmp_path / "eval"),
    )
    result = run_evaluation(config)
    assert result.run.status in {"completed", "completed_with_errors"}
    run_dir = tmp_path / "eval" / "runs" / result.run.run_id
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "reproducibility.json").exists()
    assert (run_dir / "report.md").exists()
    pass_metric = next(m for m in result.metrics if m.metric_id == "code_pass_rate")
    assert pass_metric.value == 1.0


def test_run_vision_mini(tmp_path: Path):
    config = EvaluationConfig(
        benchmark_id="vision-mini",
        model_id="development-mock-v1",
        model_provider="development_mock",
        output_dir=str(tmp_path / "vision"),
    )
    result = run_evaluation(config)
    schema = next(m for m in result.metrics if m.metric_id == "schema_validity")
    assert schema.value == 1.0


def test_run_agent_mini(tmp_path: Path):
    config = EvaluationConfig(
        benchmark_id="agent-mini",
        model_id="development-mock-v1",
        model_provider="development_mock",
        output_dir=str(tmp_path / "agent"),
    )
    result = run_evaluation(config)
    task_success = next(m for m in result.metrics if m.metric_id == "task_success")
    assert task_success.value == 1.0
