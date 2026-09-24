"""Dataset validation logic and reporting."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from training.datasets.hashing import sha256_file, sha256_text
from training.datasets.manifest import DatasetManifest
from training.datasets.records import ParsedRecord, try_parse_record


@dataclass
class ValidationIssue:
    line_number: int | None
    reason: str
    severity: str = "error"


@dataclass
class ValidationReport:
    manifest_path: str
    raw_path: str
    total_lines: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    raw_sha256: str | None = None
    token_stats: dict[str, float | int] | None = None

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def summary(self) -> str:
        lines = [
            f"Manifest: {self.manifest_path}",
            f"Raw dataset: {self.raw_path}",
            f"Total lines: {self.total_lines}",
            f"Valid records: {self.valid_records}",
            f"Invalid records: {self.invalid_records}",
            f"Duplicate records: {self.duplicate_records}",
        ]
        if self.raw_sha256:
            lines.append(f"Raw SHA-256: {self.raw_sha256}")
        if self.token_stats:
            lines.append(f"Token stats: {self.token_stats}")
        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                prefix = f"line {issue.line_number}" if issue.line_number else "manifest"
                lines.append(f"  [{issue.severity}] {prefix}: {issue.reason}")
        return "\n".join(lines)


def resolve_raw_path(manifest: DatasetManifest, manifest_path: Path) -> Path:
    raw_path = Path(manifest.records.raw_path)
    if raw_path.is_absolute():
        return raw_path
    candidates = [
        (manifest_path.parent / raw_path).resolve(),
        (Path.cwd() / raw_path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def load_jsonl_records(
    raw_path: Path,
    *,
    allow_empty_lines: bool = False,
) -> tuple[list[ParsedRecord], list[ValidationIssue]]:
    records: list[ParsedRecord] = []
    issues: list[ValidationIssue] = []
    with raw_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                if allow_empty_lines:
                    continue
                issues.append(ValidationIssue(line_number, "empty JSONL line", severity="error"))
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(
                    ValidationIssue(line_number, f"malformed JSON: {exc}", severity="error")
                )
                continue
            if not isinstance(payload, dict):
                issues.append(
                    ValidationIssue(line_number, "record must be a JSON object", severity="error")
                )
                continue
            parsed, error = try_parse_record(line_number, payload)
            if parsed is None:
                issues.append(
                    ValidationIssue(line_number, error or "invalid record", severity="error"),
                )
                continue
            records.append(parsed)
    return records, issues


def validate_manifest_and_dataset(
    manifest: DatasetManifest,
    manifest_path: Path,
    *,
    tokenizer_counter=None,
) -> ValidationReport:
    report = ValidationReport(
        manifest_path=str(manifest_path),
        raw_path=manifest.records.raw_path,
    )

    if manifest.quality.require_license and not manifest.source.license.strip():
        report.issues.append(
            ValidationIssue(None, "missing source license metadata", severity="error"),
        )

    raw_path = resolve_raw_path(manifest, manifest_path)
    report.raw_path = str(raw_path)
    if not raw_path.exists():
        report.issues.append(
            ValidationIssue(None, f"raw dataset not found: {raw_path}", severity="error")
        )
        return report

    report.raw_sha256 = sha256_file(str(raw_path))
    records, parse_issues = load_jsonl_records(raw_path)
    report.issues.extend(parse_issues)
    report.total_lines = len(records) + len(parse_issues)

    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    char_lengths: list[int] = []
    token_lengths: list[int] = []

    max_chars = manifest.preprocessing.max_chars or manifest.quality.max_chars

    for record in records:
        text = record.dedup_key
        char_lengths.append(len(text))

        if manifest.quality.reject_empty and not text.strip():
            report.issues.append(
                ValidationIssue(record.line_number, "empty example after parsing", severity="error")
            )
            report.invalid_records += 1
            continue

        if len(text) < manifest.quality.min_chars:
            report.issues.append(
                ValidationIssue(
                    record.line_number,
                    f"example shorter than min_chars ({manifest.quality.min_chars})",
                    severity="error",
                )
            )
            report.invalid_records += 1
            continue

        if len(text) > max_chars:
            report.issues.append(
                ValidationIssue(
                    record.line_number,
                    f"example exceeds max_chars ({max_chars})",
                    severity="error",
                )
            )
            report.invalid_records += 1
            continue

        if len(record.output.strip()) < manifest.quality.min_output_chars:
            report.issues.append(
                ValidationIssue(record.line_number, "output too short", severity="error")
            )
            report.invalid_records += 1
            continue

        record_id = record.record_id
        if record_id:
            if record_id in seen_ids:
                report.duplicate_records += 1
                report.issues.append(
                    ValidationIssue(
                        record.line_number,
                        f"duplicate id: {record_id}",
                        severity="error",
                    )
                )
                if not manifest.quality.allow_duplicates:
                    report.invalid_records += 1
                    continue
            seen_ids.add(record_id)

        content_hash = sha256_text(text)
        if content_hash in seen_hashes:
            report.duplicate_records += 1
            report.issues.append(
                ValidationIssue(record.line_number, "duplicate example content", severity="error")
            )
            if not manifest.quality.allow_duplicates:
                report.invalid_records += 1
                continue
        seen_hashes.add(content_hash)

        if tokenizer_counter is not None:
            token_lengths.append(tokenizer_counter(record))

        report.valid_records += 1

    if tokenizer_counter is not None and token_lengths:
        report.token_stats = {
            "count": len(token_lengths),
            "min_tokens": min(token_lengths),
            "max_tokens": max(token_lengths),
            "avg_tokens": sum(token_lengths) / len(token_lengths),
        }

    return report
