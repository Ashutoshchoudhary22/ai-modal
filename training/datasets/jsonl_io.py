"""JSONL read/write helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from training.datasets.manifest import DatasetManifest
from training.datasets.records import ParsedRecord
from training.datasets.validation import load_jsonl_records


@dataclass
class ProcessedDataset:
    manifest: DatasetManifest
    processed_dir: Path
    train_path: Path
    validation_path: Path
    test_path: Path
    train_count: int
    validation_count: int
    test_count: int
    raw_sha256: str
    processed_manifest_path: Path


def record_to_json(entry) -> dict:
    record = entry.record
    if record.kind == "conversational":
        payload = {"messages": record.messages}
    elif record.kind == "completion":
        payload = {"prompt": record.instruction, "completion": record.output}
    elif record.kind == "preference":
        payload = {
            "prompt": record.instruction,
            "chosen": record.output,
            "rejected": record.input_text,
        }
    else:
        payload = {
            "instruction": record.instruction,
            "input": record.input_text,
            "output": record.output,
        }
    if record.record_id:
        payload["id"] = record.record_id
    if record.metadata:
        payload["metadata"] = record.metadata
    return payload


def write_jsonl(path: Path, entries) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(record_to_json(entry), ensure_ascii=False) + "\n")


def load_split_records(path: Path) -> list[ParsedRecord]:
    records, issues = load_jsonl_records(path)
    if issues:
        raise ValueError(f"Processed dataset {path} has invalid records: {issues[0].reason}")
    return records
