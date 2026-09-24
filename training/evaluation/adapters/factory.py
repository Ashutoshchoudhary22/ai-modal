"""Evaluation adapter factory."""

from __future__ import annotations

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.adapters.development import DevelopmentEvaluationAdapter
from training.evaluation.errors import EvaluationError, EvaluationErrorCode


def build_adapter(
    provider: str, model_id: str, checkpoint: str | None = None
) -> EvaluationModelAdapter:
    if provider == "development_mock":
        return DevelopmentEvaluationAdapter(model_id=model_id)
    if checkpoint:
        raise EvaluationError(
            EvaluationErrorCode.MODEL_UNAVAILABLE,
            f"Checkpoint evaluation for provider {provider} is not configured in Phase 12",
        )
    raise EvaluationError(
        EvaluationErrorCode.MODEL_UNAVAILABLE,
        f"Unsupported evaluation provider: {provider}",
    )
