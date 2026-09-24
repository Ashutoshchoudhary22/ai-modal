"""Configurable deterministic dataset filtering."""

from __future__ import annotations

from dataclasses import dataclass, field

from training.datasets.manifest import DatasetManifest
from training.datasets.records import ParsedRecord


@dataclass
class FilterStats:
    input_count: int = 0
    empty_removed: int = 0
    too_long_removed: int = 0
    too_short_output_removed: int = 0
    token_limit_removed: int = 0
    remaining: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "input": self.input_count,
            "empty_removed": self.empty_removed,
            "too_long_removed": self.too_long_removed,
            "too_short_output_removed": self.too_short_output_removed,
            "token_limit_removed": self.token_limit_removed,
            "remaining": self.remaining,
        }


@dataclass
class FilterResult:
    kept: list[ParsedRecord]
    removed: list[tuple[ParsedRecord, str]] = field(default_factory=list)
    stats: FilterStats = field(default_factory=FilterStats)


def filter_records(
    records: list[ParsedRecord],
    manifest: DatasetManifest,
    *,
    tokenizer_counter=None,
    max_tokens: int | None = None,
) -> FilterResult:
    stats = FilterStats(input_count=len(records))
    kept: list[ParsedRecord] = []
    removed: list[tuple[ParsedRecord, str]] = []
    max_chars = manifest.preprocessing.max_chars or manifest.quality.max_chars

    for record in records:
        text = record.dedup_key
        if manifest.quality.reject_empty and not text.strip():
            stats.empty_removed += 1
            removed.append((record, "empty record"))
            continue
        if len(text) > max_chars:
            stats.too_long_removed += 1
            removed.append((record, f"exceeds max_chars ({max_chars})"))
            continue
        if len(record.output.strip()) < manifest.quality.min_output_chars:
            stats.too_short_output_removed += 1
            removed.append((record, "output too short"))
            continue
        if tokenizer_counter is not None and max_tokens is not None:
            token_count = tokenizer_counter(record)
            if token_count > max_tokens:
                stats.token_limit_removed += 1
                removed.append((record, f"exceeds max_tokens ({max_tokens})"))
                continue
        kept.append(record)

    stats.remaining = len(kept)
    return FilterResult(kept=kept, removed=removed, stats=stats)
