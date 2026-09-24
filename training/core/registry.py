"""Model registry integration for trained checkpoints."""

from __future__ import annotations

from ai_platform_protocol.models.registry import ModelRegistryRecord

from training.core.config import TrainingConfig
from training.core.errors import TrainingRegistryError
from training.core.experiment import ExperimentMetadata


def register_trained_model(
    config: TrainingConfig,
    experiment: ExperimentMetadata,
    *,
    checkpoint_path: str,
    context_length: int,
) -> ModelRegistryRecord:
    if not config.registry.enabled:
        raise TrainingRegistryError("Registry registration was not enabled in config")

    try:
        from ai_platform_shared.db import session_scope
        from ai_platform_shared.db.repository import ModelRegistryRepository
    except ImportError as exc:
        raise TrainingRegistryError("Shared database package is unavailable") from exc

    record = ModelRegistryRecord(
        model_id=config.registry.model_id or "",
        model_name=config.registry.model_name or config.registry.model_id or "",
        version=config.registry.version or "1.0.0",
        provider="local",
        architecture=config.model.base_model_id,
        capabilities={
            "generate": True,
            "stream": True,
            "structured": False,
            "embed": False,
            "vision": False,
            "training_experiment_id": experiment.experiment_id,
            "dataset_hash": experiment.dataset_hash,
            "smoke_test": config.experiment.smoke_test,
        },
        context_length=context_length,
        modalities=["text"],
        status=config.registry.status,
        local_path=checkpoint_path,
    )

    try:
        with session_scope() as session:
            repository = ModelRegistryRepository(session)
            return repository.upsert(record)
    except Exception as exc:
        raise TrainingRegistryError(f"Failed to register model in MySQL registry: {exc}") from exc
