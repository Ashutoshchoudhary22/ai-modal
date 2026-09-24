"""Benchmark registry."""

from __future__ import annotations

from pathlib import Path

from training.evaluation.errors import EvaluationError, EvaluationErrorCode
from training.evaluation.types import BenchmarkDefinition

_BENCHMARKS: dict[str, BenchmarkDefinition] = {}


def register(benchmark: BenchmarkDefinition) -> None:
    key = f"{benchmark.benchmark_id}@{benchmark.version}"
    _BENCHMARKS[key] = benchmark


def get(benchmark_id: str, version: str = "1.0.0") -> BenchmarkDefinition:
    key = f"{benchmark_id}@{version}"
    benchmark = _BENCHMARKS.get(key)
    if benchmark is None:
        raise EvaluationError(
            EvaluationErrorCode.BENCHMARK_NOT_FOUND,
            f"Benchmark not found: {benchmark_id}@{version}",
        )
    return benchmark


def list_benchmarks() -> list[BenchmarkDefinition]:
    return list(_BENCHMARKS.values())


def validate_benchmark(benchmark: BenchmarkDefinition) -> list[str]:
    issues: list[str] = []
    dataset_path = Path(benchmark.dataset_path)
    if not dataset_path.exists():
        issues.append(f"Dataset path not found: {dataset_path}")
    if not benchmark.metrics:
        issues.append("Benchmark must define at least one metric")
    return issues


def register_builtin_benchmarks(root: Path | None = None) -> None:
    if _BENCHMARKS:
        return
    repo_root = root or Path(__file__).resolve().parents[3]
    data = repo_root / "data" / "benchmarks"
    builtins = [
        BenchmarkDefinition(
            benchmark_id="coding-mini",
            name="Coding Mini",
            version="1.0.0",
            description="Tiny deterministic coding tasks with sandboxed tests",
            task_type="coding",
            dataset_id="coding-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "coding-mini"),
            evaluator="coding",
            metrics=["code_pass_rate", "latency_ms", "error_rate"],
            input_modality=["text"],
            output_type="code",
            max_samples=10,
            required_capabilities=["generate"],
        ),
        BenchmarkDefinition(
            benchmark_id="debugging-mini",
            name="Debugging Mini",
            version="1.0.0",
            description="Small bug-fix coding tasks",
            task_type="debugging",
            dataset_id="debugging-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "debugging-mini"),
            evaluator="coding",
            metrics=["code_pass_rate", "latency_ms", "error_rate"],
            input_modality=["text"],
            output_type="code",
            max_samples=10,
            required_capabilities=["generate"],
        ),
        BenchmarkDefinition(
            benchmark_id="vision-mini",
            name="Vision Mini",
            version="1.0.0",
            description="Tiny multimodal image understanding benchmark",
            task_type="image_understanding",
            dataset_id="vision-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "vision-mini"),
            evaluator="multimodal",
            metrics=["normalized_match", "schema_validity", "field_accuracy", "latency_ms"],
            input_modality=["text", "image"],
            output_type="structured",
            max_samples=10,
            required_capabilities=["multimodal_generate"],
        ),
        BenchmarkDefinition(
            benchmark_id="screenshot-analysis-mini",
            name="Screenshot Analysis Mini",
            version="1.0.0",
            description="Structured screenshot analysis benchmark",
            task_type="screenshot_analysis",
            dataset_id="screenshot-analysis-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "screenshot-analysis-mini"),
            evaluator="multimodal",
            metrics=["schema_validity", "field_accuracy", "latency_ms"],
            input_modality=["text", "image"],
            output_type="structured",
            max_samples=10,
            required_capabilities=["multimodal_generate"],
        ),
        BenchmarkDefinition(
            benchmark_id="screenshot-to-code-mini",
            name="Screenshot to Code Mini",
            version="1.0.0",
            description="Screenshot to rendered UI visual comparison",
            task_type="screenshot_to_code",
            dataset_id="screenshot-to-code-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "screenshot-to-code-mini"),
            evaluator="screenshot_to_code",
            metrics=["render_success", "visual_similarity", "layout_similarity", "latency_ms"],
            input_modality=["text", "image"],
            output_type="code",
            max_samples=5,
            required_capabilities=["multimodal_generate", "render"],
        ),
        BenchmarkDefinition(
            benchmark_id="agent-mini",
            name="Agent Mini",
            version="1.0.0",
            description="Deterministic agent task benchmark",
            task_type="agent_task",
            dataset_id="agent-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "agent-mini"),
            evaluator="agent",
            metrics=["task_success", "latency_ms", "error_rate"],
            input_modality=["text"],
            output_type="text",
            max_samples=10,
            required_capabilities=["agent_execute"],
        ),
        BenchmarkDefinition(
            benchmark_id="browser-agent-mini",
            name="Browser Agent Mini",
            version="1.0.0",
            description="Local fixture browser agent benchmark",
            task_type="browser_task",
            dataset_id="browser-agent-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "browser-agent-mini"),
            evaluator="browser",
            metrics=["task_success", "latency_ms", "error_rate"],
            input_modality=["text"],
            output_type="text",
            max_samples=10,
            required_capabilities=["browser_execute"],
        ),
        BenchmarkDefinition(
            benchmark_id="completion-mini",
            name="Completion Mini",
            version="1.0.0",
            description="Fill-in-the-middle code completion benchmark",
            task_type="code_completion",
            dataset_id="completion-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "completion-mini"),
            evaluator="completion",
            metrics=[
                "exact_match",
                "normalized_match",
                "prefix_preservation",
                "suffix_preservation",
                "syntax_validity",
                "latency_ms",
            ],
            input_modality=["text"],
            output_type="code",
            max_samples=10,
            required_capabilities=["complete"],
        ),
        BenchmarkDefinition(
            benchmark_id="security-prompt-injection-mini",
            name="Security Prompt Injection Mini",
            version="1.0.0",
            description="Prompt injection resistance evaluation",
            task_type="security",
            dataset_id="security-prompt-injection-mini",
            dataset_version="1.0.0",
            dataset_path=str(data / "security-prompt-injection-mini"),
            evaluator="agent",
            metrics=["policy_violation_rate", "task_success", "error_rate"],
            input_modality=["text"],
            output_type="text",
            max_samples=10,
            required_capabilities=["agent_execute"],
        ),
    ]
    for benchmark in builtins:
        register(benchmark)
