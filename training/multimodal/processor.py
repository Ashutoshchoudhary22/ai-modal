"""Multimodal training preprocessing pipeline."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from training.multimodal.config import MultimodalTrainingConfig
from training.multimodal.formatter import format_conversation
from training.multimodal.images import validate_and_load_image
from training.multimodal.records import MultimodalParsedRecord, load_jsonl_multimodal
from training.multimodal.tokenizer import CharTokenizer


@dataclass
class ImageTensorMeta:
    path: str
    width: int
    height: int
    sha256: str


@dataclass
class MultimodalTrainingExample:
    sample_id: str
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]
    pixel_values: list[float]
    image_metadata: list[ImageTensorMeta]
    assistant_start: int


class MultimodalTrainingProcessor:
    def __init__(self, config: MultimodalTrainingConfig, dataset_root: Path) -> None:
        self.config = config
        self.dataset_root = dataset_root
        self.tokenizer = CharTokenizer()
        self._fitted = False

    def fit_vocab(self, records: list[MultimodalParsedRecord]) -> None:
        texts: list[str] = []
        for record in records:
            formatted, _ = format_conversation(record, self.config.processor)
            texts.append(formatted)
            texts.append(record.assistant_text)
        self.tokenizer.build_vocab(texts)
        self._fitted = True

    def _image_to_tensor(self, image_bytes: bytes) -> list[float]:
        from PIL import Image

        size = self.config.processor.image.image_size
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")
            if self.config.processor.image.resize_mode == "center_crop":
                min_side = min(img.size)
                left = (img.width - min_side) // 2
                top = (img.height - min_side) // 2
                img = img.crop((left, top, left + min_side, top + min_side))
            img = img.resize((size, size))
            array = np.asarray(img, dtype=np.float32) / 255.0
        return array.transpose(2, 0, 1).reshape(-1).tolist()

    def process_record(self, record: MultimodalParsedRecord) -> MultimodalTrainingExample:
        if not self._fitted:
            raise RuntimeError("Processor vocabulary has not been fitted")

        formatted, assistant_start_char = format_conversation(record, self.config.processor)
        assistant_start = min(assistant_start_char + 1, len(formatted) + 1)
        encoded = self.tokenizer.encode_conversation(
            formatted,
            max_length=self.config.processor.max_seq_length,
            assistant_start=assistant_start,
        )

        image_meta: list[ImageTensorMeta] = []
        pixel_values: list[float] = []
        if record.image_paths:
            loaded = validate_and_load_image(
                self.dataset_root,
                record.image_paths[0],
                max_pixels=self.config.processor.image.max_pixels,
            )
            pixel_values = self._image_to_tensor(loaded.data)
            image_meta.append(
                ImageTensorMeta(
                    path=record.image_paths[0],
                    width=loaded.width,
                    height=loaded.height,
                    sha256=loaded.reference.sha256,
                )
            )
        else:
            size = self.config.processor.image.image_size
            pixel_values = [0.0] * (3 * size * size)

        sample_id = record.record_id or f"line-{record.line_number}"
        return MultimodalTrainingExample(
            sample_id=sample_id,
            input_ids=encoded.input_ids,
            attention_mask=encoded.attention_mask,
            labels=encoded.labels,
            pixel_values=pixel_values,
            image_metadata=image_meta,
            assistant_start=encoded.labels.index(next(v for v in encoded.labels if v != -100))
            if any(v != -100 for v in encoded.labels)
            else 0,
        )

    def process_records(
        self, records: list[MultimodalParsedRecord]
    ) -> list[MultimodalTrainingExample]:
        self.fit_vocab(records)
        return [self.process_record(record) for record in records]


def load_dataset_records(
    config: MultimodalTrainingConfig,
) -> tuple[Path, list[MultimodalParsedRecord]]:
    dataset_path = Path(config.dataset.path)
    if dataset_path.is_dir():
        jsonl_path = dataset_path / "raw.jsonl"
        if not jsonl_path.exists():
            jsonl_path = dataset_path / "train.jsonl"
        root = dataset_path
    else:
        jsonl_path = dataset_path
        root = dataset_path.parent
    records = load_jsonl_multimodal(jsonl_path)
    if config.dataset.max_records is not None:
        records = records[: config.dataset.max_records]
    return root, records
