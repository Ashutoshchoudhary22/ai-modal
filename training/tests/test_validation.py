from pathlib import Path

from training.datasets.manifest import load_manifest
from training.datasets.records import parse_record, try_parse_record
from training.datasets.validation import validate_manifest_and_dataset


def test_parse_instruction_record():
    record = parse_record(1, {"instruction": "Do x", "input": "", "output": "code"})
    assert record.kind == "instruction"


def test_reject_empty_output():
    parsed, error = try_parse_record(1, {"instruction": "x", "input": "", "output": "  "})
    assert parsed is None
    assert error


def test_validate_smoke_dataset():
    manifest = load_manifest("training/data/manifests/smoke_sft.json")
    report = validate_manifest_and_dataset(
        manifest,
        Path("training/data/manifests/smoke_sft.json"),
    )
    assert report.valid_records == 10
    assert report.passed


def test_validation_fails_on_duplicates(tmp_path: Path):
    raw = tmp_path / "dup.jsonl"
    raw.write_text(
        Path("training/tests/fixtures/duplicate_examples.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest = load_manifest("training/data/manifests/smoke_sft.json")
    manifest.records.raw_path = str(raw)
    report = validate_manifest_and_dataset(manifest, tmp_path / "manifest.json")
    assert not report.passed
    assert report.duplicate_records >= 1
