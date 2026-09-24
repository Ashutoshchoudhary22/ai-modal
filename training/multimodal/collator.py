"""Batch collation for multimodal training examples."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from training.multimodal.config import MultimodalTrainingConfig
from training.multimodal.processor import MultimodalTrainingExample
from training.multimodal.tokenizer import CharTokenizer


@dataclass
class MultimodalBatch:
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    labels: torch.Tensor
    pixel_values: torch.Tensor
    sample_ids: list[str]


class MultimodalDataCollator:
    def __init__(self, tokenizer: CharTokenizer, config: MultimodalTrainingConfig) -> None:
        self.tokenizer = tokenizer
        self.image_size = config.processor.image.image_size

    def __call__(self, examples: list[MultimodalTrainingExample]) -> MultimodalBatch:
        if not examples:
            raise ValueError("Cannot collate empty batch")

        encoded = [
            type(
                "Enc",
                (),
                {
                    "input_ids": example.input_ids,
                    "labels": example.labels,
                    "attention_mask": example.attention_mask,
                },
            )()
            for example in examples
        ]
        input_ids, labels, attention_mask = self.tokenizer.pad_batch(encoded)

        pixel_tensors = []
        for example in examples:
            channels = 3
            size = self.image_size
            expected = channels * size * size
            values = example.pixel_values
            if len(values) != expected:
                raise ValueError(
                    f"Sample {example.sample_id} has incompatible pixel_values length "
                    f"{len(values)} != {expected}"
                )
            pixel_tensors.append(
                torch.tensor(values, dtype=torch.float32).reshape(channels, size, size)
            )

        return MultimodalBatch(
            input_ids=torch.tensor(input_ids, dtype=torch.long),
            attention_mask=torch.tensor(attention_mask, dtype=torch.long),
            labels=torch.tensor(labels, dtype=torch.long),
            pixel_values=torch.stack(pixel_tensors, dim=0),
            sample_ids=[example.sample_id for example in examples],
        )
