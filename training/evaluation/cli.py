"""Evaluation CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from training.evaluation.benchmarks.registry import (
    list_benchmarks,
    register_builtin_benchmarks,
    validate_benchmark,
)
from training.evaluation.comparison.compare import compare_results
from training.evaluation.config import EvaluationConfig, load_evaluation_config
from training.evaluation.errors import EvaluationError
from training.evaluation.reports.generator import (
    render_comparison_markdown,
    render_markdown,
)
from training.evaluation.runners.runner import run_evaluation
from training.evaluation.types import EvaluationResult, MetricValue


def _load_result(run_dir: Path) -> EvaluationResult:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    metrics_raw = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    from training.evaluation.types import EvaluationRun

    run = EvaluationRun(
        run_id=summary["run_id"],
        benchmark_id=summary["benchmark_id"],
        benchmark_version=summary["benchmark_version"],
        model_id=summary["model_id"],
        model_provider=summary.get("model_provider", "development_mock"),
        dataset_fingerprint="",
        status=summary["status"],
        complete=summary.get("complete", False),
    )
    metrics = [MetricValue.model_validate(item) for item in metrics_raw]
    return EvaluationResult(
        run=run,
        metrics=metrics,
        sample_results=[],
        errors=summary.get("errors", 0),
        completed_samples=summary.get("completed_samples", 0),
        total_samples=summary.get("total_samples", 0),
        warnings=summary.get("warnings", []),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Platform evaluation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-benchmarks", help="List registered benchmarks")

    validate = sub.add_parser("validate", help="Validate a benchmark")
    validate.add_argument("--benchmark", required=True)

    run = sub.add_parser("run", help="Run a benchmark evaluation")
    run.add_argument("--benchmark", required=True)
    run.add_argument("--model", default="development-mock-v1")
    run.add_argument("--provider", default="development_mock")
    run.add_argument("--config", help="Optional YAML config path")
    run.add_argument("--output-dir", default="training/output/evaluation")
    run.add_argument("--model-checkpoint")
    run.add_argument("--dry-run", action="store_true")

    compare = sub.add_parser("compare", help="Compare two evaluation runs")
    compare.add_argument("--run-a", required=True)
    compare.add_argument("--run-b", required=True)

    report = sub.add_parser("report", help="Render report for a run")
    report.add_argument("--run", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    register_builtin_benchmarks()

    try:
        if args.command == "list-benchmarks":
            for benchmark in list_benchmarks():
                print(
                    f"{benchmark.benchmark_id}@{benchmark.version} "
                    f"task={benchmark.task_type} dataset={benchmark.dataset_id} "
                    f"metrics={','.join(benchmark.metrics)}"
                )
            return 0

        if args.command == "validate":
            from training.evaluation.benchmarks.registry import get

            benchmark = get(args.benchmark)
            issues = validate_benchmark(benchmark)
            if issues:
                print("INVALID:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
            print(f"Benchmark {args.benchmark} is valid")
            return 0

        if args.command == "run":
            if args.config:
                config = load_evaluation_config(args.config)
            else:
                config = EvaluationConfig(
                    benchmark_id=args.benchmark,
                    model_id=args.model,
                    model_provider=args.provider,
                    model_checkpoint=args.model_checkpoint,
                    output_dir=args.output_dir,
                )
            result = run_evaluation(config, dry_run=args.dry_run)
            if args.dry_run:
                print("Dry run complete.")
            else:
                print(f"Evaluation complete: {result.run.status}")
            return 0

        if args.command == "compare":
            result_a = _load_result(Path(args.run_a))
            result_b = _load_result(Path(args.run_b))
            rows = compare_results(result_a, result_b)
            print(render_comparison_markdown(rows, result_a.run.model_id, result_b.run.model_id))
            return 0

        if args.command == "report":
            run_dir = Path(args.run)
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            result = _load_result(run_dir)
            print(render_markdown(result))
            print(f"Summary: {summary['status']}")
            return 0
    except EvaluationError as exc:
        print(f"ERROR [{exc.code}]: {exc.message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
