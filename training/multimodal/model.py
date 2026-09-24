"""Trainable tiny multimodal model for development training."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import torch
import torch.nn as nn
import torch.nn.functional as F

from training.multimodal.config import ModelSection
from training.multimodal.tokenizer import CharTokenizer


@dataclass
class ParameterReport:
    total_parameters: int
    trainable_parameters: int
    frozen_parameters: int

    @property
    def trainable_percentage(self) -> float:
        if self.total_parameters == 0:
            return 0.0
        return 100.0 * self.trainable_parameters / self.total_parameters


class TrainableMultimodalModel(Protocol):
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        pixel_values: torch.Tensor,
        labels: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]: ...

    def trainable_parameters(self) -> ParameterReport: ...

    def parameter_count(self) -> int: ...

    def save_pretrained(self, path: str) -> None: ...

    @classmethod
    def load_pretrained(
        cls, path: str, config: ModelSection, vocab_size: int
    ) -> TrainableMultimodalModel: ...


class TinyImageEncoder(nn.Module):
    def __init__(self, image_size: int, hidden_dim: int) -> None:
        super().__init__()
        flat_dim = 3 * image_size * image_size
        self.proj = nn.Sequential(
            nn.Linear(flat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        batch_size, channels, height, width = pixel_values.shape
        flat = pixel_values.reshape(batch_size, channels * height * width)
        return self.proj(flat)


class TinyMultimodalModel(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        image_size: int,
        config: ModelSection,
    ) -> None:
        super().__init__()
        hidden_dim = config.language_model.hidden_dim
        self.config = config
        self.image_encoder = TinyImageEncoder(image_size, config.vision_encoder.hidden_dim)
        self.projector = nn.Linear(config.vision_encoder.hidden_dim, hidden_dim)
        self.token_embedding = nn.Embedding(vocab_size, hidden_dim)
        self.lm_head = nn.Linear(hidden_dim, vocab_size)
        self.image_size = image_size

        if config.freeze_vision_encoder:
            for param in self.image_encoder.parameters():
                param.requires_grad = False
        if config.freeze_projector:
            for param in self.projector.parameters():
                param.requires_grad = False
        if config.freeze_language_model:
            for param in self.token_embedding.parameters():
                param.requires_grad = False
            for param in self.lm_head.parameters():
                param.requires_grad = False

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        pixel_values: torch.Tensor,
        labels: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        text_hidden = self.token_embedding(input_ids)
        image_hidden = self.projector(self.image_encoder(pixel_values)).unsqueeze(1)
        hidden = torch.cat([image_hidden, text_hidden], dim=1)

        image_mask = torch.ones(
            (attention_mask.shape[0], 1),
            dtype=attention_mask.dtype,
            device=attention_mask.device,
        )
        full_mask = torch.cat([image_mask, attention_mask], dim=1)
        hidden = hidden * full_mask.unsqueeze(-1)

        logits = self.lm_head(hidden)
        output: dict[str, torch.Tensor] = {"logits": logits}
        if labels is not None:
            image_labels = torch.full(
                (labels.shape[0], 1),
                -100,
                dtype=labels.dtype,
                device=labels.device,
            )
            full_labels = torch.cat([image_labels, labels], dim=1)
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = full_labels[..., 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,
            )
            output["loss"] = loss
        return output

    def trainable_parameters(self) -> ParameterReport:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return ParameterReport(
            total_parameters=total,
            trainable_parameters=trainable,
            frozen_parameters=total - trainable,
        )

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def save_pretrained(self, path: str) -> None:
        import json
        from pathlib import Path

        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), target / "model.pt")
        (target / "model_config.json").write_text(
            json.dumps(self.config.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_pretrained(
        cls, path: str, config: ModelSection, vocab_size: int
    ) -> TinyMultimodalModel:
        from pathlib import Path

        model = cls(vocab_size=vocab_size, image_size=32, config=config)
        state_path = Path(path) / "model.pt"
        if state_path.exists():
            state = torch.load(state_path, map_location="cpu", weights_only=True)
            model.load_state_dict(state)
        return model


def build_model(
    config: ModelSection,
    tokenizer: CharTokenizer,
    image_size: int,
) -> TinyMultimodalModel:
    vocab_size = config.language_model.vocab_size or tokenizer.vocab_size
    if config.type not in {"tiny_multimodal", "development_mock"}:
        raise ValueError(f"Unsupported model type: {config.type}")
    return TinyMultimodalModel(vocab_size=vocab_size, image_size=image_size, config=config)
