"""Training configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from training.core.errors import TrainingConfigError


class ExperimentConfig(BaseModel):
    name: str
    description: str = ""
    seed: int = 42
    smoke_test: bool = False


class ModelConfig(BaseModel):
    base_model_id: str
    trust_remote_code: bool = False


class TokenizerConfig(BaseModel):
    model_id: str | None = None
    use_fast: bool = True


class DatasetTrainingConfig(BaseModel):
    manifest: str
    dataset_id: str | None = None
    dataset_version: str | None = None
    reuse_processed: bool = True
    processed_dir: str | None = None


class OutputConfig(BaseModel):
    dir: str
    save_total_limit: int = 2


class TrainingParams(BaseModel):
    num_epochs: int = Field(default=1, ge=1)
    per_device_train_batch_size: int = Field(default=1, ge=1)
    per_device_eval_batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=1, ge=1)
    learning_rate: float = Field(default=5e-5, gt=0)
    max_seq_length: int = Field(default=512, ge=16)
    warmup_ratio: float = Field(default=0.0, ge=0, lt=1)
    weight_decay: float = Field(default=0.0, ge=0)
    logging_steps: int = Field(default=10, ge=1)
    save_strategy: Literal["no", "epoch", "steps"] = "epoch"
    eval_strategy: Literal["no", "epoch", "steps"] = "epoch"
    save_steps: int = Field(default=500, ge=1)
    eval_steps: int = Field(default=500, ge=1)
    gradient_checkpointing: bool = False


class LoRAConfig(BaseModel):
    enabled: bool = False
    rank: int = Field(default=16, ge=1)
    alpha: int = Field(default=32, ge=1)
    dropout: float = Field(default=0.05, ge=0, lt=1)
    target_modules: list[str] = Field(default_factory=list)
    quantization: Literal["none", "4bit", "8bit"] = "none"


class HardwareConfig(BaseModel):
    device: str = "auto"
    precision: Literal["auto", "fp32", "fp16", "bf16"] = "auto"


class RegistryConfig(BaseModel):
    enabled: bool = False
    model_id: str | None = None
    model_name: str | None = None
    version: str | None = None
    status: str = "registered"


class WandbConfig(BaseModel):
    enabled: bool = False
    project: str = "ai-platform"
    run_name: str | None = None


class PromptTemplateConfig(BaseModel):
    instruction: str = "### Instruction:\n{instruction}"
    input: str = "### Input:\n{input}"
    response: str = "### Response:\n{output}"


class TrainingConfig(BaseModel):
    experiment: ExperimentConfig
    model: ModelConfig
    tokenizer: TokenizerConfig = Field(default_factory=TokenizerConfig)
    dataset: DatasetTrainingConfig
    output: OutputConfig
    training: TrainingParams = Field(default_factory=TrainingParams)
    lora: LoRAConfig = Field(default_factory=LoRAConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)
    wandb: WandbConfig = Field(default_factory=WandbConfig)
    prompt_template: PromptTemplateConfig = Field(default_factory=PromptTemplateConfig)

    @model_validator(mode="after")
    def validate_registry(self) -> TrainingConfig:
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
        if self.lora.enabled and not self.lora.target_modules and self.lora.quantization != "none":
            pass
        return self


def load_training_config(path: str | Path) -> TrainingConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise TrainingConfigError(f"Training config not found: {config_path}")
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TrainingConfigError("Training config must be a YAML mapping")
    try:
        return TrainingConfig.model_validate(data)
    except Exception as exc:
        raise TrainingConfigError(f"Invalid training config: {exc}") from exc


def resolve_repo_path(path: str, base: Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    root = base or Path.cwd()
    return (root / candidate).resolve()
