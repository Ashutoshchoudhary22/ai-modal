"""Dataset inspection without dumping full content."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from training.datasets.dedup import deduplicate_records
from training.datasets.records import ParsedRecord
from training.datasets.validation import load_jsonl_records


@dataclass
class InspectReport:
    path: str
    dataset_type: str = "unknown"
    format: str = "jsonl"
    record_count: int = 0
    invalid_count: int = 0
    field_counts: dict[str, int] = field(default_factory=dict)
    char_lengths: list[int] = field(default_factory=list)
    token_lengths: list[int] = field(default_factory=list)
    exact_duplicates: int = 0
    normalized_duplicates: int = 0
    samples: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Dataset: {self.path}",
            f"Type: {self.dataset_type}",
            f"Format: {self.format}",
            f"Records: {self.record_count}",
            f"Invalid: {self.invalid_count}",
        ]
        if self.field_counts:
            lines.append("Fields:")
            for name, count in sorted(self.field_counts.items()):
                lines.append(f"  {name}: {count}")
        if self.char_lengths:
            lines.extend(
                [
                    "Length (chars):",
                    f"  min: {min(self.char_lengths)}",
                    f"  max: {max(self.char_lengths)}",
                    f"  mean: {sum(self.char_lengths) / len(self.char_lengths):.1f}",
                ]
            )
        if self.token_lengths:
            lines.extend(
                [
                    "Length (tokens):",
                    f"  min: {min(self.token_lengths)}",
                    f"  max: {max(self.token_lengths)}",
                    f"  mean: {sum(self.token_lengths) / len(self.token_lengths):.1f}",
                ]
            )
        lines.extend(
            [
                "Duplicates:",
                f"  exact: {self.exact_duplicates}",
                f"  normalized: {self.normalized_duplicates}",
            ]
        )
        if self.samples:
            lines.append("Sample:")
            for sample in self.samples:
                lines.append(f"  {sample[:200]}")
        return "\n".join(lines)


def _infer_type(records: list[ParsedRecord]) -> str:
    kinds = {record.kind for record in records}
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


def _field_counts(records: list[ParsedRecord]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        if record.kind == "instruction":
            counter.update(["instruction", "input", "output"])
        elif record.kind == "conversational":
            counter["messages"] += 1
        elif record.kind == "completion":
            counter.update(["prompt", "completion"])
        elif record.kind == "preference":
            counter.update(["prompt", "chosen", "rejected"])
    return dict(counter)


def inspect_dataset(
    path: Path,
    *,
    sample_size: int = 3,
    tokenizer_counter=None,
) -> InspectReport:
    records, issues = load_jsonl_records(path)
    dedup = deduplicate_records(records)
    report = InspectReport(
        path=str(path),
        dataset_type=_infer_type(records),
        record_count=len(records),
        invalid_count=len(issues),
        field_counts=_field_counts(records),
        char_lengths=[len(record.dedup_key) for record in records],
        exact_duplicates=len(
            [reason for _, reason in dedup.removed if reason == "exact duplicate"]
        ),
        normalized_duplicates=len(
            [reason for _, reason in dedup.removed if reason == "normalized-text duplicate"]
        ),
    )
    if tokenizer_counter is not None:
        report.token_lengths = [tokenizer_counter(record) for record in records]
    report.samples = [record.dedup_key[:200] for record in records[:sample_size]]
    return report
