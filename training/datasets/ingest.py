"""Dataset ingestion and end-to-end processing."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from training.datasets.clean import clean_records
from training.datasets.dedup import deduplicate_records
from training.datasets.filter import filter_records
from training.datasets.fingerprint import (
    fingerprint_config,
    fingerprint_normalized_records,
    fingerprint_processed_splits,
    fingerprint_raw_file,
)
from training.datasets.jsonl_io import ProcessedDataset, write_jsonl
from training.datasets.leakage import detect_split_leakage
from training.datasets.manifest import DatasetManifest, save_manifest
from training.datasets.report import QualityReport
from training.datasets.split import split_records
from training.datasets.storage import FilesystemDatasetStorage
from training.datasets.validation import load_jsonl_records, resolve_raw_path


@dataclass
class IngestResult:
    processed: ProcessedDataset
    quality_report: QualityReport
    leakage_passed: bool


def process_dataset(
    manifest: DatasetManifest,
    manifest_path: Path,
    *,
    processed_dir: Path | None = None,
    tokenizer_counter=None,
    max_tokens: int | None = None,
) -> IngestResult:
    started = time.perf_counter()
    raw_path = resolve_raw_path(manifest, manifest_path)
    raw_sha256 = fingerprint_raw_file(raw_path)
    config_hash = fingerprint_config(manifest)

    records, parse_issues = load_jsonl_records(raw_path)
    input_count = len(records) + len(parse_issues)

    cleaned, clean_rejected = clean_records(records, manifest)
    filtered = filter_records(
        cleaned,
        manifest,
        tokenizer_counter=tokenizer_counter,
        max_tokens=max_tokens,
    )
    deduped = deduplicate_records(filtered.kept)
    split = split_records(deduped.kept, manifest.split)
    leakage = detect_split_leakage(split.train, split.validation, split.test)

    target_dir = processed_dir
    if target_dir is None:
        if manifest.records.processed_dir:
            target_dir = Path(manifest.records.processed_dir)
        else:
            target_dir = (
                Path("training/data/processed")
                / manifest.dataset.name
                / manifest.dataset.version
            )
    storage = FilesystemDatasetStorage(target_dir)
    target_dir = storage.resolve(".")

    train_path = target_dir / "train.jsonl"
    validation_path = target_dir / "validation.jsonl"
    test_path = target_dir / "test.jsonl"
    write_jsonl(train_path, split.train)
    write_jsonl(validation_path, split.validation)
    write_jsonl(test_path, split.test)

    normalized_hash = fingerprint_normalized_records([entry.record for entry in deduped.kept])
    processed_hash = fingerprint_processed_splits(train_path, validation_path, test_path)

    processed_manifest = manifest.model_copy(deep=True)
    processed_manifest.records = processed_manifest.records.model_copy(
        update={
            "processed_dir": str(target_dir),
            "count": len(deduped.kept),
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        }
    )
    processed_manifest.provenance = processed_manifest.provenance.model_copy(
        update={
            "raw_sha256": raw_sha256,
            "normalized_sha256": normalized_hash,
            "processed_sha256": processed_hash,
            "processing_config_hash": config_hash,
            "processing_version": processed_manifest.preprocessing.version,
            "source_reference": manifest.source.url,
            "parent_version": manifest.dataset.parent_version,
        }
    )
    processed_manifest_path = target_dir / "manifest.json"
    save_manifest(processed_manifest, processed_manifest_path)

    exact_dupes = len(
        [item for item in deduped.removed if item[1] == "exact duplicate"]
    )
    norm_dupes = len(
        [item for item in deduped.removed if item[1] == "normalized-text duplicate"]
    )
    filtered_count = len(filtered.removed) + len(clean_rejected)

    quality = QualityReport(
        dataset_name=manifest.dataset.name,
        dataset_version=manifest.dataset.version,
        input_records=input_count,
        valid_records=len(records),
        invalid_records=len(parse_issues),
        exact_duplicates=exact_dupes,
        normalized_duplicates=norm_dupes,
        filtered_records=filtered_count,
        output_records=len(deduped.kept),
        train_records=len(split.train),
        validation_records=len(split.validation),
        test_records=len(split.test),
        raw_hash=raw_sha256,
        normalized_hash=normalized_hash,
        processed_hash=processed_hash,
        configuration_hash=config_hash,
        processing_duration_sec=time.perf_counter() - started,
        warnings=[] if leakage.passed else [leakage.summary()],
        errors=[issue.reason for issue in parse_issues if issue.severity == "error"],
        metadata={"run_id": str(uuid.uuid4())},
    )
    quality.write(target_dir / "quality_report.json")

    processed = ProcessedDataset(
        manifest=processed_manifest,
        processed_dir=target_dir,
        train_path=train_path,
        validation_path=validation_path,
        test_path=test_path,
        train_count=len(split.train),
        validation_count=len(split.validation),
        test_count=len(split.test),
        raw_sha256=raw_sha256,
        processed_manifest_path=processed_manifest_path,
    )
    return IngestResult(
        processed=processed,
        quality_report=quality,
        leakage_passed=leakage.passed,
    )
