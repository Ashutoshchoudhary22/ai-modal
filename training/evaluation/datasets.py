"""Benchmark dataset loading and fingerprinting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from training.datasets.hashing import sha256_text


def load_benchmark_samples(dataset_path: Path) -> list[dict[str, Any]]:
    jsonl_path = dataset_path / "samples.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Missing samples.jsonl in {dataset_path}")
    samples: list[dict[str, Any]] = []
    with jsonl_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            payload["_line_number"] = line_number
            samples.append(payload)
    return samples


def fingerprint_benchmark_dataset(samples: list[dict[str, Any]]) -> str:
    keys = [json.dumps(sample, sort_keys=True, ensure_ascii=False) for sample in samples]
    return sha256_text("\n".join(keys))
