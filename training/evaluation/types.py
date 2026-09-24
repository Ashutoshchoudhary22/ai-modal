"""Evaluation protocol types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MetricDirection = Literal["higher_is_better", "lower_is_better"]
RunStatus = Literal[
    "created",
    "validating",
    "running",
    "completed",
    "completed_with_errors",
    "failed",
    "cancelled",
]
SampleStatus = Literal["completed", "failed", "skipped", "error"]
FailureCategory = Literal[
    "MODEL_ERROR",
    "INVALID_OUTPUT",
    "SCHEMA_ERROR",
    "EXECUTION_ERROR",
    "TIMEOUT",
    "TOOL_ERROR",
    "POLICY_DENIED",
    "BROWSER_ERROR",
    "RENDER_ERROR",
    "COMPARISON_ERROR",
    "DATASET_ERROR",
    "CAPABILITY_UNSUPPORTED",
]


class MetricDefinition(BaseModel):
    metric_id: str
    name: str
    version: int = 1
    description: str
    direction: MetricDirection
    range_min: float | None = None
    range_max: float | None = None


class MetricValue(BaseModel):
    metric_id: str
    metric_version: int
    value: float | None
    sample_count: int
    direction: MetricDirection
    unavailable: bool = False


class BenchmarkDefinition(BaseModel):
    benchmark_id: str
    name: str
    version: str
    description: str
    task_type: str
    dataset_id: str
    dataset_version: str
    dataset_path: str
    evaluator: str
    metrics: list[str]
    input_modality: list[str] = Field(default_factory=lambda: ["text"])
    output_type: str = "text"
    max_samples: int | None = None
    required_capabilities: list[str] = Field(default_factory=list)


class GenerationConfig(BaseModel):
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 1024
    seed: int = 42
    structured_output: bool = False


class ResourceLimits(BaseModel):
    max_samples: int | None = None
    max_runtime_sec: float | None = None
    max_model_calls: int | None = None
    max_agent_iterations: int | None = None
    max_tool_calls: int | None = None
    max_browser_actions: int | None = None
    max_sample_retries: int = 0
    code_timeout_sec: float = 5.0


class EvaluationSampleResult(BaseModel):
    sample_id: str
    prediction: str | dict[str, Any] | None = None
    reference: str | dict[str, Any] | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    latency_ms: float | None = None
    token_usage: dict[str, int | None] = Field(default_factory=dict)
    error: str | None = None
    failure_category: FailureCategory | None = None
    status: SampleStatus = "completed"
    attempt_count: int = 1


class EvaluationRun(BaseModel):
    run_id: str
    benchmark_id: str
    benchmark_version: str
    model_id: str
    model_provider: str
    model_checkpoint: str | None = None
    dataset_fingerprint: str
    config: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus = "created"
    seed: int = 42
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    complete: bool = False


class EvaluationResult(BaseModel):
    run: EvaluationRun
    metrics: list[MetricValue]
    sample_results: list[EvaluationSampleResult]
    errors: int = 0
    completed_samples: int = 0
    total_samples: int = 0
    warnings: list[str] = Field(default_factory=list)
