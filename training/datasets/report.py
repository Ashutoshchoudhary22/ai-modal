"""Machine-readable dataset quality reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class QualityReport:
    dataset_name: str
    dataset_version: str
    input_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    exact_duplicates: int = 0
    normalized_duplicates: int = 0
    filtered_records: int = 0
    output_records: int = 0
    train_records: int = 0
    validation_records: int = 0
    test_records: int = 0
    raw_hash: str | None = None
    normalized_hash: str | None = None
    processed_hash: str | None = None
    configuration_hash: str | None = None
    processing_duration_sec: float | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def summary(self) -> str:
        lines = [
            f"Dataset: {self.dataset_name} v{self.dataset_version}",
            f"Input records: {self.input_records}",
            f"Valid records: {self.valid_records}",
            f"Invalid records: {self.invalid_records}",
            f"Exact duplicates removed: {self.exact_duplicates}",
            f"Normalized duplicates removed: {self.normalized_duplicates}",
            f"Filtered records: {self.filtered_records}",
            f"Output records: {self.output_records}",
            f"Train/val/test: {self.train_records}/{self.validation_records}/{self.test_records}",
        ]
        if self.raw_hash:
            lines.append(f"Raw SHA-256: {self.raw_hash}")
        if self.processed_hash:
            lines.append(f"Processed SHA-256: {self.processed_hash}")
        if self.configuration_hash:
            lines.append(f"Config hash: {self.configuration_hash}")
        if self.processing_duration_sec is not None:
            lines.append(f"Duration: {self.processing_duration_sec:.2f}s")
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {w}" for w in self.warnings)
        if self.errors:
            lines.append("Errors:")
            lines.extend(f"  - {e}" for e in self.errors)
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path
