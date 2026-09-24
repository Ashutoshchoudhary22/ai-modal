"""Checkpoint metadata and artifact management."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from training.core.config import TrainingConfig
from training.core.experiment import ExperimentMetadata


@dataclass
class CheckpointMetadata:
    model_path: str
    base_model: str
    dataset_manifest: str
    dataset_id: str | None
    dataset_version: str | None
    dataset_hash: str
    processing_config_hash: str | None
    experiment_id: str
    seed: int
    training_config: dict[str, Any]
    smoke_test: bool


def prepare_output_dir(config: TrainingConfig) -> Path:
    output_dir = Path(config.output.dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_training_metadata(
    output_dir: Path,
    *,
    config: TrainingConfig,
    experiment: ExperimentMetadata,
    dataset_manifest_path: Path,
    dataset_hash: str,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    processing_config_hash: str | None = None,
) -> Path:
    metadata = CheckpointMetadata(
        model_path=str(output_dir),
        base_model=config.model.base_model_id,
        dataset_manifest=str(dataset_manifest_path),
        dataset_id=dataset_id or config.dataset.dataset_id,
        dataset_version=dataset_version or config.dataset.dataset_version,
        dataset_hash=dataset_hash,
        processing_config_hash=processing_config_hash,
        experiment_id=experiment.experiment_id,
        seed=config.experiment.seed,
        training_config=config.model_dump(mode="json"),
        smoke_test=config.experiment.smoke_test,
    )
    path = output_dir / "training_metadata.json"
    path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    return path


def copy_config_snapshot(config_path: Path, output_dir: Path) -> Path:
    target = output_dir / "training_config.yaml"
    shutil.copy2(config_path, target)
    return target
