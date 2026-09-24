"""Structured evaluation errors."""

from __future__ import annotations

from enum import StrEnum


class EvaluationErrorCode(StrEnum):
    EVAL_CONFIG_INVALID = "eval_config_invalid"
    BENCHMARK_NOT_FOUND = "benchmark_not_found"
    BENCHMARK_INVALID = "benchmark_invalid"
    BENCHMARK_CAPABILITY_UNSUPPORTED = "benchmark_capability_unsupported"
    BENCHMARK_CONTAMINATION_WARNING = "benchmark_contamination_warning"
    DATASET_INVALID = "dataset_invalid"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_ERROR = "model_error"
    INVALID_OUTPUT = "invalid_output"
    SCHEMA_ERROR = "schema_error"
    EXECUTION_ERROR = "execution_error"
    EXECUTION_TIMEOUT = "execution_timeout"
    TOOL_ERROR = "tool_error"
    POLICY_DENIED = "policy_denied"
    BROWSER_ERROR = "browser_error"
    RENDER_ERROR = "render_error"
    COMPARISON_ERROR = "comparison_error"
    EVALUATION_CANCELLED = "evaluation_cancelled"
    EVALUATION_FAILED = "evaluation_failed"


class EvaluationError(Exception):
    def __init__(
        self,
        code: EvaluationErrorCode,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
