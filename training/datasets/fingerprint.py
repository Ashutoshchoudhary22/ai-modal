"""Deterministic dataset fingerprinting."""

from __future__ import annotations

from pathlib import Path

from training.datasets.dedup import normalized_dedup_key
from training.datasets.hashing import sha256_bytes, sha256_file, sha256_text
from training.datasets.manifest import DatasetManifest
from training.datasets.records import ParsedRecord


def fingerprint_raw_file(path: Path) -> str:
    return sha256_file(str(path))


def fingerprint_normalized_records(records: list[ParsedRecord]) -> str:
    parts = sorted(normalized_dedup_key(record) for record in records)
    return sha256_text("\n".join(parts))


def fingerprint_processed_splits(*paths: Path) -> str:
    digests: list[str] = []
    for path in sorted(paths, key=lambda p: p.name):
        if path.exists():
            digests.append(sha256_file(str(path)))
    return sha256_bytes("\n".join(digests).encode("utf-8"))


def fingerprint_config(manifest: DatasetManifest) -> str:
    payload = manifest.model_dump(mode="json")
    return sha256_text(str(sorted(payload.items())))
