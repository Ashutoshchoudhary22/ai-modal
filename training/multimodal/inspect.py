"""Inspect processed multimodal training examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from training.multimodal.config import load_multimodal_config
from training.multimodal.processor import MultimodalTrainingProcessor, load_dataset_records
from training.multimodal.tokenizer import IGNORE_INDEX
from training.multimodal.validation import validate_jsonl_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect multimodal training samples")
    parser.add_argument("--config", help="Optional training config path")
    parser.add_argument("--dataset", required=True, help="Dataset directory or JSONL path")
    parser.add_argument("--index", type=int, default=0, help="Sample index to inspect")
    parser.add_argument("--preview", type=int, default=0, help="Preview first N samples")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dataset_path = Path(args.dataset)

    if args.config:
        config = load_multimodal_config(args.config)
        config.dataset.path = str(dataset_path)
        dataset_root = dataset_path if dataset_path.is_dir() else dataset_path.parent
        records, _ = validate_jsonl_dataset(
            dataset_root,
            dataset_id=dataset_path.name,
            version="1.0.0",
        )
        processor = MultimodalTrainingProcessor(config, dataset_root)
        examples = processor.process_records(records)
    else:
        from training.multimodal.config import (
            DatasetSection,
            ExperimentSection,
            MultimodalTrainingConfig,
            OutputSection,
        )

        config = MultimodalTrainingConfig(
            experiment=ExperimentSection(name="inspect"),
            dataset=DatasetSection(path=str(dataset_path)),
            output=OutputSection(dir="."),
        )
        dataset_root, records = load_dataset_records(config)
        processor = MultimodalTrainingProcessor(config, dataset_root)
        examples = processor.process_records(records)

    if args.preview > 0:
        for idx, example in enumerate(examples[: args.preview]):
            masked = sum(1 for label in example.labels if label == IGNORE_INDEX)
            trainable = sum(1 for label in example.labels if label != IGNORE_INDEX)
            print(
                json.dumps(
                    {
                        "index": idx,
                        "sample_id": example.sample_id,
                        "token_count": len(example.input_ids),
                        "label_mask": {"ignored": masked, "trainable": trainable},
                        "image_metadata": [meta.__dict__ for meta in example.image_metadata],
                    },
                    indent=2,
                )
            )
        return 0

    if args.index < 0 or args.index >= len(examples):
        print(f"Index out of range: {args.index}", file=sys.stderr)
        return 1

    example = examples[args.index]
    masked = sum(1 for label in example.labels if label == IGNORE_INDEX)
    trainable = sum(1 for label in example.labels if label != IGNORE_INDEX)
    print(
        json.dumps(
            {
                "sample_id": example.sample_id,
                "token_count": len(example.input_ids),
                "label_mask": {"ignored": masked, "trainable": trainable},
                "image_metadata": [meta.__dict__ for meta in example.image_metadata],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
