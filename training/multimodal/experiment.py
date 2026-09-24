"""Experiment metadata and reproducibility manifest."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from training.multimodal.config import MultimodalTrainingConfig

RunStatus = Literal[
    "created",
    "validating",
    "preparing",
    "running",
    "evaluating",
    "saving",
    "completed",
    "failed",
    "cancelled",
]

_VALID_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    "created": {"validating", "failed", "cancelled"},
    "validating": {"preparing", "failed", "cancelled"},
    "preparing": {"running", "failed", "cancelled"},
    "running": {"evaluating", "saving", "completed", "failed", "cancelled"},
    "evaluating": {"running", "saving", "failed", "cancelled"},
    "saving": {"running", "completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


@dataclass
class MultimodalExperimentMetadata:
    experiment_id: str
    run_id: str
    dataset_id: str
    dataset_version: str
    dataset_fingerprint: str
    model_id: str
    training_config: dict[str, Any]
    seed: int
    created_at: str
    status: RunStatus = "created"
    checkpoint_path: str | None = None
    git_commit: str | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    hardware: dict[str, Any] = field(default_factory=dict)
    metrics_summary: dict[str, Any] = field(default_factory=dict)


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
    versions = {"python": sys.version.split()[0], "platform": platform.platform()}
    for package in ("torch", "numpy"):
        try:
            module = __import__(package)
            versions[package] = getattr(module, "__version__", "unknown")
        except ImportError:
            continue
    return versions


def start_experiment(
    config: MultimodalTrainingConfig,
    *,
    dataset_id: str,
    dataset_version: str,
    dataset_fingerprint: str,
    device: str,
) -> MultimodalExperimentMetadata:
    return MultimodalExperimentMetadata(
        experiment_id=str(uuid.uuid4()),
        run_id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_fingerprint=dataset_fingerprint,
        model_id=config.model.type,
        training_config=config.model_dump(mode="json"),
        seed=config.experiment.seed,
        created_at=datetime.now(UTC).isoformat(),
        git_commit=_git_revision(),
        environment=_software_versions(),
        hardware={"device": device, "dtype": config.hardware.dtype},
    )


def transition_status(current: RunStatus, new_status: RunStatus) -> RunStatus:
    allowed = _VALID_TRANSITIONS[current]
    if new_status not in allowed and current != new_status:
        raise ValueError(f"Invalid status transition: {current} -> {new_status}")
    return new_status


def write_reproducibility_manifest(
    output_dir: Path,
    experiment: MultimodalExperimentMetadata,
    config: MultimodalTrainingConfig,
    *,
    dataset_fingerprint: str,
) -> Path:
    payload = {
        "experiment_id": experiment.experiment_id,
        "run_id": experiment.run_id,
        "seed": experiment.seed,
        "dataset": {
            "id": experiment.dataset_id,
            "version": experiment.dataset_version,
            "fingerprint": dataset_fingerprint,
        },
        "model": config.model.model_dump(mode="json"),
        "processor": config.processor.model_dump(mode="json"),
        "training_config": config.training.model_dump(mode="json"),
        "software_versions": experiment.environment,
        "device": experiment.hardware.get("device"),
        "dtype": experiment.hardware.get("dtype"),
    }
    path = output_dir / "reproducibility.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def save_experiment(output_dir: Path, experiment: MultimodalExperimentMetadata) -> Path:
    path = output_dir / "experiment.json"
    path.write_text(json.dumps(asdict(experiment), indent=2), encoding="utf-8")
    return path
