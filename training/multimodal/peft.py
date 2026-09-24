"""Lightweight LoRA support for development multimodal models."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from training.multimodal.config import PeftSection
from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode


@dataclass
class PeftReport:
    target_modules: list[str]
    trainable_parameters: int
    total_parameters: int


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, rank: int, alpha: int, dropout: float) -> None:
        super().__init__()
        self.base = base
        self.base.weight.requires_grad = False
        if self.base.bias is not None:
            self.base.bias.requires_grad = False
        self.rank = rank
        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout)
        self.lora_a = nn.Linear(base.in_features, rank, bias=False)
        self.lora_b = nn.Linear(rank, base.out_features, bias=False)
        nn.init.zeros_(self.lora_b.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.base(x) + self.lora_b(self.lora_a(self.dropout(x))) * self.scaling


def _module_path_matches(name: str, target: str) -> bool:
    return name == target or name.endswith(f".{target}") or name.split(".")[-1] == target


def apply_lora(model: nn.Module, config: PeftSection) -> PeftReport:
    if config.dropout < 0 or config.dropout >= 1:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.PEFT_TARGET_MODULE_NOT_FOUND,
            "LoRA dropout must be in [0, 1)",
        )
    if not config.target_modules:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.PEFT_TARGET_MODULE_NOT_FOUND,
            "PEFT target_modules must not be empty",
        )

    matched: list[str] = []
    for name, module in list(model.named_modules()):
        if not isinstance(module, nn.Linear):
            continue
        if not any(_module_path_matches(name, target) for target in config.target_modules):
            continue
        parent_name, child_name = name.rsplit(".", 1) if "." in name else ("", name)
        parent = model.get_submodule(parent_name) if parent_name else model
        setattr(parent, child_name, LoRALinear(module, config.rank, config.alpha, config.dropout))
        matched.append(name)

    if not matched:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.PEFT_TARGET_MODULE_NOT_FOUND,
            f"No target modules matched: {config.target_modules}",
            details={"target_modules": config.target_modules},
        )

    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return PeftReport(
        target_modules=matched, trainable_parameters=trainable, total_parameters=total
    )
