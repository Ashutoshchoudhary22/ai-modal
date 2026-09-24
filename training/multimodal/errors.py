"""Structured errors for multimodal training."""

from __future__ import annotations

from enum import StrEnum


class MultimodalTrainingErrorCode(StrEnum):
    TRAINING_CONFIG_INVALID = "training_config_invalid"
    DATASET_INVALID = "dataset_invalid"
    DATASET_LEAKAGE = "dataset_leakage"
    IMAGE_INVALID = "image_invalid"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_ARCHITECTURE_INVALID = "model_architecture_invalid"
    PROCESSOR_INVALID = "processor_invalid"
    COLLATOR_INVALID = "collator_invalid"
    PEFT_TARGET_MODULE_NOT_FOUND = "peft_target_module_not_found"
    CHECKPOINT_INCOMPATIBLE = "checkpoint_incompatible"
    CHECKPOINT_CORRUPTED = "checkpoint_corrupted"
    INSUFFICIENT_DISK_SPACE = "insufficient_disk_space"
    DEVICE_UNAVAILABLE = "device_unavailable"
    TRAINING_OUT_OF_MEMORY = "training_out_of_memory"
    TRAINING_CANCELLED = "training_cancelled"
    TRAINING_FAILED = "training_failed"


class MultimodalTrainingError(Exception):
    def __init__(
        self,
        code: MultimodalTrainingErrorCode,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
