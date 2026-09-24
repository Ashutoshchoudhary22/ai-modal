"""Multimodal training configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode


class ExperimentSection(BaseModel):
    name: str
    description: str = ""
    seed: int = 42
    smoke_test: bool = False


class DatasetSection(BaseModel):
    path: str
    manifest: str | None = None
    split: Literal["train", "validation", "test", "all"] = "train"
    max_records: int | None = Field(default=None, ge=1)
    max_images: int | None = Field(default=None, ge=1)


class ImageProcessorSection(BaseModel):
    image_size: int = Field(default=32, ge=8)
    resize_mode: Literal["resize", "center_crop"] = "resize"
    max_pixels: int = Field(default=262_144, ge=1)
    dtype: Literal["fp32", "fp16", "bf16"] = "fp32"


class ProcessorSection(BaseModel):
    chat_template: str = "<{role}>\n{content}\n</{role}>"
    image_token: str = "<image>"
    max_seq_length: int = Field(default=256, ge=16)
    image: ImageProcessorSection = Field(default_factory=ImageProcessorSection)


class VisionEncoderSection(BaseModel):
    type: Literal["tiny", "mock"] = "tiny"
    hidden_dim: int = Field(default=64, ge=8)


class ProjectorSection(BaseModel):
    type: Literal["linear", "identity"] = "linear"
    hidden_dim: int = Field(default=64, ge=8)


class LanguageModelSection(BaseModel):
    type: Literal["tiny", "mock"] = "tiny"
    hidden_dim: int = Field(default=64, ge=8)
    vocab_size: int | None = None


class ModelSection(BaseModel):
    type: Literal["tiny_multimodal", "development_mock"] = "tiny_multimodal"
    vision_encoder: VisionEncoderSection = Field(default_factory=VisionEncoderSection)
    projector: ProjectorSection = Field(default_factory=ProjectorSection)
    language_model: LanguageModelSection = Field(default_factory=LanguageModelSection)
    freeze_vision_encoder: bool = False
    freeze_language_model: bool = False
    freeze_projector: bool = False
    trust_remote_code: bool = False


class TrainingSection(BaseModel):
    training_mode: Literal["full", "lora"] = "full"
    num_epochs: int = Field(default=1, ge=1)
    max_steps: int | None = Field(default=None, ge=1)
    per_device_train_batch_size: int = Field(default=1, ge=1)
    per_device_eval_batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=1, ge=1)
    learning_rate: float = Field(default=1e-3, gt=0)
    weight_decay: float = Field(default=0.0, ge=0)
    warmup_steps: int = Field(default=0, ge=0)
    warmup_ratio: float = Field(default=0.0, ge=0, lt=1)
    max_grad_norm: float = Field(default=1.0, gt=0)
    logging_steps: int = Field(default=1, ge=1)
    eval_steps: int = Field(default=2, ge=1)
    save_steps: int = Field(default=2, ge=1)
    save_total_limit: int = Field(default=2, ge=1)
    gradient_checkpointing: bool = False
    scheduler: Literal["linear", "cosine", "constant"] = "linear"
    optimizer: Literal["adamw", "sgd"] = "adamw"


class PeftSection(BaseModel):
    enabled: bool = False
    method: Literal["lora"] = "lora"
    rank: int = Field(default=4, ge=1)
    alpha: int = Field(default=8, ge=1)
    dropout: float = Field(default=0.05, ge=0, lt=1)
    target_modules: list[str] = Field(default_factory=lambda: ["lm_head"])


class HardwareSection(BaseModel):
    device: str = "cpu"
    dtype: Literal["fp32", "fp16", "bf16"] = "fp32"


class OutputSection(BaseModel):
    dir: str
    save_total_limit: int = Field(default=2, ge=1)


class ResourceLimits(BaseModel):
    max_training_steps: int | None = Field(default=None, ge=1)
    max_dataset_records: int | None = Field(default=None, ge=1)
    max_images: int | None = Field(default=None, ge=1)
    max_runtime_sec: float | None = Field(default=None, gt=0)
    min_free_disk_bytes: int = Field(default=10_485_760, ge=0)


class RegistrySection(BaseModel):
    enabled: bool = False
    model_id: str | None = None
    model_name: str | None = None
    version: str | None = None
    status: str = "registered"


class EvaluationSection(BaseModel):
    enabled: bool = True
    metric: str = "loss"
    lower_is_better: bool = True


class MultimodalTrainingConfig(BaseModel):
    experiment: ExperimentSection
    dataset: DatasetSection
    model: ModelSection = Field(default_factory=ModelSection)
    processor: ProcessorSection = Field(default_factory=ProcessorSection)
    training: TrainingSection = Field(default_factory=TrainingSection)
    peft: PeftSection = Field(default_factory=PeftSection)
    hardware: HardwareSection = Field(default_factory=HardwareSection)
    output: OutputSection
    resources: ResourceLimits = Field(default_factory=ResourceLimits)
    registry: RegistrySection = Field(default_factory=RegistrySection)
    evaluation: EvaluationSection = Field(default_factory=EvaluationSection)

    @model_validator(mode="after")
    def validate_training_mode(self) -> MultimodalTrainingConfig:
        if self.training.training_mode == "lora" and not self.peft.enabled:
            self.peft.enabled = True
        if self.peft.enabled and self.training.training_mode != "lora":
            self.training.training_mode = "lora"
        if self.model.trust_remote_code:
            raise ValueError("trust_remote_code must remain false by default")
        return self

    @model_validator(mode="after")
    def validate_registry(self) -> MultimodalTrainingConfig:
        if self.registry.enabled:
            missing = [
                name
                for name, value in {
                    "registry.model_id": self.registry.model_id,
                    "registry.model_name": self.registry.model_name,
                    "registry.version": self.registry.version,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(f"Registry enabled but missing fields: {', '.join(missing)}")
        return self


def load_multimodal_config(path: str | Path) -> MultimodalTrainingConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.TRAINING_CONFIG_INVALID,
            f"Config not found: {config_path}",
        )
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        return MultimodalTrainingConfig.model_validate(raw)
    except Exception as exc:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.TRAINING_CONFIG_INVALID,
            f"Invalid multimodal training config: {exc}",
        ) from exc
