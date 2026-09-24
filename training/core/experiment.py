"""Experiment metadata tracking."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from training.core.config import TrainingConfig
from training.core.hardware import TrainingHardwareInfo


@dataclass
class ExperimentMetadata:
    experiment_id: str
    name: str
    description: str
    started_at: str
    base_model: str
    dataset_name: str
    dataset_version: str
    dataset_hash: str
    training_config_path: str
    seed: int
    ended_at: str | None = None
    hardware: dict[str, Any] = field(default_factory=dict)
    software_versions: dict[str, str] = field(default_factory=dict)
    git_revision: str | None = None
    training_metrics: dict[str, Any] = field(default_factory=dict)
    validation_metrics: dict[str, Any] = field(default_factory=dict)
    checkpoint_path: str | None = None
    smoke_test: bool = False


def _git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _software_versions() -> dict[str, str]:
    versions = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    for package in ("torch", "transformers", "peft", "accelerate"):
        try:
            module = __import__(package)
            versions[package] = getattr(module, "__version__", "unknown")
        except ImportError:
            continue
    return versions


def start_experiment(
    config: TrainingConfig,
    config_path: Path,
    *,
    dataset_name: str,
    dataset_version: str,
    dataset_hash: str,
    hardware: TrainingHardwareInfo,
) -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment_id=str(uuid.uuid4()),
        name=config.experiment.name,
        description=config.experiment.description,
        started_at=datetime.now(UTC).isoformat(),
        base_model=config.model.base_model_id,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        training_config_path=str(config_path),
        seed=config.experiment.seed,
        hardware=asdict(hardware),
        software_versions=_software_versions(),
        git_revision=_git_revision(),
        smoke_test=config.experiment.smoke_test,
    )


def finalize_experiment(
    metadata: ExperimentMetadata,
    *,
    checkpoint_path: Path,
    training_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
) -> ExperimentMetadata:
    metadata.ended_at = datetime.now(UTC).isoformat()
    metadata.checkpoint_path = str(checkpoint_path)
    metadata.training_metrics = training_metrics
    metadata.validation_metrics = validation_metrics
    return metadata


def save_experiment_metadata(metadata: ExperimentMetadata, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "experiment.json"
    path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    return path
