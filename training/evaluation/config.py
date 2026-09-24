"""Evaluation configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from training.evaluation.errors import EvaluationError, EvaluationErrorCode
from training.evaluation.types import GenerationConfig, ResourceLimits


class EvaluationConfig(BaseModel):
    benchmark_id: str
    model_id: str = "development-mock-v1"
    model_provider: str = "development_mock"
    model_checkpoint: str | None = None
    output_dir: str = "training/output/evaluation"
    seed: int = 42
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    resources: ResourceLimits = Field(default_factory=ResourceLimits)
    training_dataset_fingerprint: str | None = None
    baseline_run_id: str | None = None


def load_evaluation_config(path: str | Path) -> EvaluationConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise EvaluationError(
            EvaluationErrorCode.EVAL_CONFIG_INVALID,
            f"Config not found: {config_path}",
        )
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        return EvaluationConfig.model_validate(raw)
    except Exception as exc:
        raise EvaluationError(
            EvaluationErrorCode.EVAL_CONFIG_INVALID,
            f"Invalid evaluation config: {exc}",
        ) from exc
