"""End-to-end dataset preprocessing pipeline."""

from __future__ import annotations

from pathlib import Path

from training.datasets.ingest import process_dataset
from training.datasets.jsonl_io import ProcessedDataset, load_split_records, write_jsonl
from training.datasets.manifest import DatasetManifest

__all__ = [
    "ProcessedDataset",
    "load_split_records",
    "preprocess_dataset",
    "write_jsonl",
]


def preprocess_dataset(
    manifest: DatasetManifest,
    manifest_path: Path,
    *,
    processed_dir: Path | None = None,
) -> ProcessedDataset:
    result = process_dataset(
        manifest,
        manifest_path,
        processed_dir=processed_dir,
    )
    return result.processed
