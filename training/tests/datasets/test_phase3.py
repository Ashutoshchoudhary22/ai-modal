"""Phase 3 dataset system tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from training.datasets.dedup import deduplicate_records, normalize_for_dedup
from training.datasets.filter import filter_records
from training.datasets.fingerprint import (
    fingerprint_config,
    fingerprint_raw_file,
)
from training.datasets.ingest import process_dataset
from training.datasets.inspect import inspect_dataset
from training.datasets.leakage import detect_split_leakage
from training.datasets.manifest import load_manifest
from training.datasets.records import parse_record
from training.datasets.report import QualityReport
from training.datasets.split import split_records
from training.datasets.storage import FilesystemDatasetStorage
from training.datasets.validation import load_jsonl_records

EXAMPLES = Path(__file__).resolve().parents[3] / "data" / "examples"
MANIFEST = EXAMPLES / "coding-mini.manifest.json"
JSONL = EXAMPLES / "coding-mini.jsonl"


def test_manifest_loads():
    manifest = load_manifest(MANIFEST)
    assert manifest.dataset.name == "coding-mini"
    assert manifest.deduplication.normalized is True


def test_parse_instruction_and_preference():
    instruction = parse_record(1, {"instruction": "A", "input": "", "output": "x"})
    assert instruction.kind == "instruction"
    preference = parse_record(
        2,
        {"prompt": "p", "chosen": "good", "rejected": "bad"},
    )
    assert preference.kind == "preference"


def test_normalized_dedup_collapses_whitespace_variants():
    records = [
        parse_record(1, {"instruction": "A", "input": "", "output": "print('x')"}),
        parse_record(2, {"instruction": "A", "input": "", "output": "print('x')"}),
        parse_record(3, {"instruction": "A", "input": "", "output": "print( 'x' )"}),
    ]
    result = deduplicate_records(records)
    assert len(result.kept) == 1
    assert len(result.removed) == 2


def test_normalize_for_dedup_deterministic():
    assert normalize_for_dedup("a\n\nb") == normalize_for_dedup("a  b")


def test_fingerprint_stable():
    h1 = fingerprint_raw_file(JSONL)
    h2 = fingerprint_raw_file(JSONL)
    assert h1 == h2


def test_fingerprint_changes_with_content(tmp_path: Path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text('{"instruction":"x","input":"","output":"y"}\n', encoding="utf-8")
    b.write_text('{"instruction":"x","input":"","output":"z"}\n', encoding="utf-8")
    assert fingerprint_raw_file(a) != fingerprint_raw_file(b)


def test_filter_empty_records():
    manifest = load_manifest(MANIFEST)
    records = [
        parse_record(1, {"instruction": "A", "input": "", "output": "ok"}),
        parse_record(2, {"instruction": "B", "input": "", "output": "x"}),
    ]
    manifest.quality.min_output_chars = 2
    result = filter_records(records, manifest)
    assert result.stats.remaining == 1
    assert result.stats.too_short_output_removed == 1


def test_split_no_overlap():
    manifest = load_manifest(MANIFEST)
    records, _ = load_jsonl_records(JSONL)
    from training.datasets.dedup import deduplicate_records

    entries = deduplicate_records(records).kept
    split = split_records(entries, manifest.split)
    leakage = detect_split_leakage(split.train, split.validation, split.test)
    assert leakage.passed


def test_process_dataset_end_to_end(tmp_path: Path):
    manifest = load_manifest(MANIFEST)
    manifest.records.raw_path = str(JSONL)
    result = process_dataset(manifest, MANIFEST, processed_dir=tmp_path / "out")
    assert result.processed.train_path.exists()
    assert (tmp_path / "out" / "quality_report.json").exists()
    assert result.quality_report.output_records > 0
    assert result.quality_report.configuration_hash == fingerprint_config(manifest)


def test_inspect_dataset():
    report = inspect_dataset(JSONL)
    assert report.record_count > 0
    assert "Records:" in report.summary()


def test_storage_blocks_path_traversal(tmp_path: Path):
    storage = FilesystemDatasetStorage(tmp_path)
    storage.write_text("safe/file.txt", "ok")
    with pytest.raises(ValueError):
        storage.resolve("../escape.txt")


def test_quality_report_json_roundtrip():
    report = QualityReport(dataset_name="x", dataset_version="1.0.0", input_records=10)
    data = json.loads(report.to_json())
    assert data["dataset_name"] == "x"


def test_malformed_jsonl_detected(tmp_path: Path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    _, issues = load_jsonl_records(path)
    assert issues


def test_unicode_record(tmp_path: Path):
    path = tmp_path / "unicode.jsonl"
    path.write_text(
        '{"instruction":"café","input":"","output":"print(\\"café\\")"}\n',
        encoding="utf-8",
    )
    records, issues = load_jsonl_records(path)
    assert records
    assert not issues


@pytest.mark.integration
def test_dataset_metadata_persist_optional(tmp_path: Path):
    import importlib.util

    if importlib.util.find_spec("pymysql") is None:
        pytest.skip("pymysql not installed")
    manifest = load_manifest(MANIFEST)
    manifest.records.raw_path = str(JSONL)
    result = process_dataset(manifest, MANIFEST, processed_dir=tmp_path / "db-out")
    from training.datasets.metadata import persist_dataset_metadata

    version_id = persist_dataset_metadata(manifest, result)
    if version_id is None:
        pytest.skip("MySQL dataset metadata not available")
