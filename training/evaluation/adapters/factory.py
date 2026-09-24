"""Evaluation adapter factory."""

from __future__ import annotations

import os

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.adapters.development import DevelopmentEvaluationAdapter
from training.evaluation.adapters.local import LocalEvaluationAdapter
from training.evaluation.errors import EvaluationError, EvaluationErrorCode


def build_adapter(
    provider: str, model_id: str, checkpoint: str | None = None
) -> EvaluationModelAdapter:
    if provider == "development_mock":
        return DevelopmentEvaluationAdapter(model_id=model_id)
    if provider == "local":
        api_url = os.getenv("AI_PLATFORM_EVAL_API_URL", "http://127.0.0.1:8000")
        return LocalEvaluationAdapter(model_id=model_id, api_url=api_url)
    if checkpoint:
        raise EvaluationError(
            EvaluationErrorCode.MODEL_UNAVAILABLE,
            f"Checkpoint evaluation for provider {provider} is not configured in Phase 12",
        )
    raise EvaluationError(
        EvaluationErrorCode.MODEL_UNAVAILABLE,
        f"Unsupported evaluation provider: {provider}",
    )
