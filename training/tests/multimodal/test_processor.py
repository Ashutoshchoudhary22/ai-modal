from pathlib import Path

from training.multimodal.config import (
    DatasetSection,
    ExperimentSection,
    MultimodalTrainingConfig,
    OutputSection,
)
from training.multimodal.processor import MultimodalTrainingProcessor
from training.multimodal.tokenizer import IGNORE_INDEX
from training.multimodal.validation import validate_jsonl_dataset


def _config() -> MultimodalTrainingConfig:
    return MultimodalTrainingConfig(
        experiment=ExperimentSection(name="test"),
        dataset=DatasetSection(path="data/examples/multimodal-mini"),
        output=OutputSection(dir="."),
    )


def test_label_masking_ignores_user_tokens():
    records, _ = validate_jsonl_dataset(
        Path("data/examples/multimodal-mini"),
        dataset_id="multimodal-mini",
        version="1.0.0",
    )
    processor = MultimodalTrainingProcessor(_config(), Path("data/examples/multimodal-mini"))
    example = processor.process_records(records[:1])[0]
    ignored = sum(1 for label in example.labels if label == IGNORE_INDEX)
    trainable = sum(1 for label in example.labels if label != IGNORE_INDEX)
    assert ignored > 0
    assert trainable > 0
