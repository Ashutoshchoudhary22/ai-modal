"""Checkpoint save/load and resume compatibility."""

from __future__ import annotations

import json
import random
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from training.multimodal.config import MultimodalTrainingConfig
from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode


@dataclass
class MultimodalCheckpointMetadata:
    step: int
    epoch: int
    dataset_fingerprint: str
    model_config: dict[str, Any]
    training_config: dict[str, Any]
    processor_config: dict[str, Any]
    tokenizer_vocab: dict[str, int]
    best_validation_loss: float | None = None
    random_state: dict[str, Any] | None = None


def _capture_random_state() -> dict[str, Any]:
    np_state = np.random.get_state()
    state: dict[str, Any] = {
        "python": random.getstate(),
        "numpy": (np_state[0], np_state[1].tolist(), np_state[2], np_state[3], np_state[4]),
    }
    if torch is not None:
        state["torch"] = torch.get_rng_state().tolist()
    return state


def _to_tuple(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_to_tuple(item) for item in value)
    return value


def _restore_random_state(state: dict[str, Any]) -> None:
    random.setstate(_to_tuple(state["python"]))
    np_tuple = state["numpy"]
    if isinstance(np_tuple, list):
        np_tuple = tuple(np_tuple)
    np.random.set_state((np_tuple[0], np.array(np_tuple[1]), np_tuple[2], np_tuple[3], np_tuple[4]))
    if "torch" in state:
        torch.set_rng_state(torch.tensor(state["torch"], dtype=torch.uint8))


def verify_disk_space(path: Path, min_free_bytes: int) -> None:
    target = path if path.is_dir() else path.parent
    target.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(target)
    if usage.free < min_free_bytes:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.INSUFFICIENT_DISK_SPACE,
            f"Insufficient disk space: {usage.free} < {min_free_bytes}",
        )


def save_checkpoint(
    output_dir: Path,
    *,
    step: int,
    epoch: int,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    config: MultimodalTrainingConfig,
    dataset_fingerprint: str,
    tokenizer_vocab: dict[str, int],
    best_validation_loss: float | None,
    name: str,
) -> Path:
    verify_disk_space(output_dir, config.resources.min_free_disk_bytes)
    checkpoint_dir = output_dir / name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), checkpoint_dir / "model.pt")
    torch.save(optimizer.state_dict(), checkpoint_dir / "optimizer.pt")
    if scheduler is not None:
        torch.save(scheduler.state_dict(), checkpoint_dir / "scheduler.pt")

    metadata = MultimodalCheckpointMetadata(
        step=step,
        epoch=epoch,
        dataset_fingerprint=dataset_fingerprint,
        model_config=config.model.model_dump(mode="json"),
        training_config=config.training.model_dump(mode="json"),
        processor_config=config.processor.model_dump(mode="json"),
        tokenizer_vocab=tokenizer_vocab,
        best_validation_loss=best_validation_loss,
        random_state=_capture_random_state(),
    )
    (checkpoint_dir / "checkpoint_metadata.json").write_text(
        json.dumps(asdict(metadata), indent=2),
        encoding="utf-8",
    )
    (checkpoint_dir / "training_config.json").write_text(
        json.dumps(config.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return checkpoint_dir


def load_checkpoint_metadata(checkpoint_dir: Path) -> MultimodalCheckpointMetadata:
    path = checkpoint_dir / "checkpoint_metadata.json"
    if not path.exists():
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.CHECKPOINT_CORRUPTED,
            f"Missing checkpoint metadata: {path}",
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return MultimodalCheckpointMetadata(**data)


def validate_resume_compatibility(
    metadata: MultimodalCheckpointMetadata,
    config: MultimodalTrainingConfig,
    dataset_fingerprint: str,
) -> None:
    mismatches: list[str] = []
    if metadata.dataset_fingerprint != dataset_fingerprint:
        mismatches.append("dataset_fingerprint")
    if metadata.model_config != config.model.model_dump(mode="json"):
        mismatches.append("model_config")
    if metadata.processor_config != config.processor.model_dump(mode="json"):
        mismatches.append("processor_config")
    critical_training = {
        "training_mode": config.training.training_mode,
        "learning_rate": config.training.learning_rate,
        "per_device_train_batch_size": config.training.per_device_train_batch_size,
    }
    saved_training = metadata.training_config
    for key, value in critical_training.items():
        if saved_training.get(key) != value:
            mismatches.append(f"training.{key}")
    if mismatches:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.CHECKPOINT_INCOMPATIBLE,
            f"Checkpoint incompatible fields: {', '.join(mismatches)}",
            details={"fields": mismatches},
        )


def apply_checkpoint_retention(
    output_dir: Path, save_total_limit: int, active_checkpoint: Path
) -> None:
    checkpoints = sorted(
        [path for path in output_dir.glob("checkpoint-*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
    )
    while len(checkpoints) > save_total_limit:
        candidate = checkpoints.pop(0)
        if candidate.resolve() == active_checkpoint.resolve():
            continue
        shutil.rmtree(candidate, ignore_errors=True)


def restore_training_state(
    checkpoint_dir: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
) -> MultimodalCheckpointMetadata:
    metadata = load_checkpoint_metadata(checkpoint_dir)
    model_state = torch.load(checkpoint_dir / "model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(model_state)
    optimizer_state = torch.load(
        checkpoint_dir / "optimizer.pt", map_location="cpu", weights_only=True
    )
    optimizer.load_state_dict(optimizer_state)
    scheduler_path = checkpoint_dir / "scheduler.pt"
    if scheduler is not None and scheduler_path.exists():
        scheduler_state = torch.load(scheduler_path, map_location="cpu", weights_only=True)
        scheduler.load_state_dict(scheduler_state)
    if metadata.random_state:
        _restore_random_state(metadata.random_state)
    return metadata
