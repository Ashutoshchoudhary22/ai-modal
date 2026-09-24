"""Deterministic dataset deduplication."""

from __future__ import annotations

import json
from dataclasses import dataclass

from training.datasets.hashing import sha256_text
from training.datasets.records import ParsedRecord


@dataclass
class DedupEntry:
    record: ParsedRecord
    original_hash: str
    normalized_hash: str


@dataclass
class DedupResult:
    kept: list[DedupEntry]
    removed: list[tuple[ParsedRecord, str]]


def normalize_for_dedup(text: str) -> str:
    return "".join(text.split())


def normalized_dedup_key(record: ParsedRecord) -> str:
    if record.kind == "conversational":
        normalized_messages = [
            {"role": message["role"], "content": normalize_for_dedup(message["content"])}
            for message in record.messages
        ]
        return json.dumps(normalized_messages, sort_keys=True, ensure_ascii=False)
    if record.kind == "completion":
        return "\n".join(
            [
                normalize_for_dedup(record.instruction),
                normalize_for_dedup(record.output),
            ]
        )
    if record.kind == "preference":
        return "\n".join(
            [
                normalize_for_dedup(record.instruction),
                normalize_for_dedup(record.output),
                normalize_for_dedup(record.input_text),
            ]
        )
    return "\n".join(
        [
            normalize_for_dedup(record.instruction),
            normalize_for_dedup(record.input_text),
            normalize_for_dedup(record.output),
        ]
    )


def deduplicate_records(records: list[ParsedRecord]) -> DedupResult:
    kept: list[DedupEntry] = []
    removed: list[tuple[ParsedRecord, str]] = []
    seen_original: set[str] = set()
    seen_normalized: set[str] = set()

    for record in records:
        original_hash = sha256_text(record.dedup_key)
        normalized_hash = sha256_text(normalized_dedup_key(record))

        if original_hash in seen_original:
            removed.append((record, "exact duplicate"))
            continue
        if normalized_hash in seen_normalized:
            removed.append((record, "normalized-text duplicate"))
            continue

        seen_original.add(original_hash)
        seen_normalized.add(normalized_hash)
        kept.append(
            DedupEntry(
                record=record,
                original_hash=original_hash,
                normalized_hash=normalized_hash,
            )
        )

    return DedupResult(kept=kept, removed=removed)
