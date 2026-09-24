"""Dataset validation, quality reporting, and leakage detection."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from training.datasets.hashing import sha256_text
from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode
from training.multimodal.images import validate_and_load_image
from training.multimodal.records import MultimodalParsedRecord, parse_multimodal_record


@dataclass
class ValidationIssue:
    dataset: str
    record_id: str | None
    line_number: int | None
    field: str
    error_code: str
    message: str


@dataclass
class MultimodalQualityReport:
    dataset_id: str
    version: str
    fingerprint: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    image_count: int = 0
    unique_image_count: int = 0
    duplicate_image_count: int = 0
    avg_width: float = 0.0
    avg_height: float = 0.0
    max_width: int = 0
    max_height: int = 0
    avg_images_per_record: float = 0.0
    task_distribution: dict[str, int] = field(default_factory=dict)
    split_distribution: dict[str, int] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.invalid_records == 0 and not self.issues


@dataclass
class ImageLeakageReport:
    train_image_hashes: set[str]
    validation_image_hashes: set[str]
    test_image_hashes: set[str]
    overlapping_hashes: set[str]

    @property
    def passed(self) -> bool:
        return not self.overlapping_hashes


def validate_jsonl_dataset(
    dataset_path: Path,
    *,
    dataset_id: str,
    version: str,
    max_images_per_record: int = 4,
) -> tuple[list[MultimodalParsedRecord], MultimodalQualityReport]:
    issues: list[ValidationIssue] = []
    records: list[MultimodalParsedRecord] = []
    seen_ids: set[str] = set()
    image_hashes: list[str] = []
    widths: list[int] = []
    heights: list[int] = []
    task_distribution: Counter[str] = Counter()

    raw_path = dataset_path / "raw.jsonl" if dataset_path.is_dir() else dataset_path
    if not raw_path.exists():
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.DATASET_INVALID,
            f"Dataset file not found: {raw_path}",
        )

    with raw_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=None,
                        line_number=line_number,
                        field="line",
                        error_code="EMPTY_LINE",
                        message="Empty JSONL line",
                    )
                )
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=None,
                        line_number=line_number,
                        field="line",
                        error_code="MALFORMED_JSON",
                        message=str(exc),
                    )
                )
                continue

            try:
                record = parse_multimodal_record(line_number, payload)
            except Exception as exc:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=payload.get("id"),
                        line_number=line_number,
                        field="record",
                        error_code="INVALID_RECORD",
                        message=str(exc),
                    )
                )
                continue

            if not record.record_id:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=None,
                        line_number=line_number,
                        field="id",
                        error_code="MISSING_ID",
                        message="Record id is required",
                    )
                )
            elif record.record_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=record.record_id,
                        line_number=line_number,
                        field="id",
                        error_code="DUPLICATE_ID",
                        message=f"Duplicate record id: {record.record_id}",
                    )
                )
            else:
                seen_ids.add(record.record_id)

            if len(record.image_paths) > max_images_per_record:
                issues.append(
                    ValidationIssue(
                        dataset=dataset_id,
                        record_id=record.record_id,
                        line_number=line_number,
                        field="images",
                        error_code="EXCESSIVE_IMAGE_COUNT",
                        message=f"Too many images: {len(record.image_paths)}",
                    )
                )

            for image_path in record.image_paths:
                try:
                    loaded = validate_and_load_image(
                        dataset_path if dataset_path.is_dir() else dataset_path.parent, image_path
                    )
                    image_hashes.append(loaded.reference.sha256)
                    widths.append(loaded.width)
                    heights.append(loaded.height)
                except MultimodalTrainingError as exc:
                    issues.append(
                        ValidationIssue(
                            dataset=dataset_id,
                            record_id=record.record_id,
                            line_number=line_number,
                            field="image",
                            error_code=str(exc.details.get("error_code", exc.code)),
                            message=exc.message,
                        )
                    )

            task = str(record.metadata.get("task_type", "image_understanding"))
            task_distribution[task] += 1
            records.append(record)

    hash_counter = Counter(image_hashes)
    duplicate_image_count = sum(count - 1 for count in hash_counter.values() if count > 1)
    fingerprint = sha256_text(
        json.dumps([record.dedup_key for record in records], sort_keys=True, ensure_ascii=False)
    )

    report = MultimodalQualityReport(
        dataset_id=dataset_id,
        version=version,
        fingerprint=fingerprint,
        total_records=len(records) + len([i for i in issues if i.error_code != "EMPTY_LINE"]),
        valid_records=len(records) if not issues else len(records),
        invalid_records=len(issues),
        image_count=len(image_hashes),
        unique_image_count=len(set(image_hashes)),
        duplicate_image_count=duplicate_image_count,
        avg_width=(sum(widths) / len(widths)) if widths else 0.0,
        avg_height=(sum(heights) / len(heights)) if heights else 0.0,
        max_width=max(widths) if widths else 0,
        max_height=max(heights) if heights else 0,
        avg_images_per_record=(len(image_hashes) / len(records)) if records else 0.0,
        task_distribution=dict(task_distribution),
        issues=issues,
    )
    if issues:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.DATASET_INVALID,
            f"Dataset validation failed with {len(issues)} issue(s)",
            details={"issues": [issue.__dict__ for issue in issues]},
        )
    return records, report


def detect_image_leakage(
    train_hashes: set[str],
    validation_hashes: set[str],
    test_hashes: set[str],
) -> ImageLeakageReport:
    overlapping = (
        (train_hashes & validation_hashes)
        | (train_hashes & test_hashes)
        | (validation_hashes & test_hashes)
    )
    return ImageLeakageReport(
        train_image_hashes=train_hashes,
        validation_image_hashes=validation_hashes,
        test_image_hashes=test_hashes,
        overlapping_hashes=overlapping,
    )


def fingerprint_dataset(
    records: list[MultimodalParsedRecord], processor_config: dict[str, Any]
) -> str:
    payload = {
        "records": [record.dedup_key for record in records],
        "processor": processor_config,
    }
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))
