"""Multimodal training strategy — Phase 11."""

from training.multimodal.config import MultimodalTrainingConfig, load_multimodal_config
from training.multimodal.trainer import run_multimodal_training

__all__ = ["MultimodalTrainingConfig", "load_multimodal_config", "run_multimodal_training"]
