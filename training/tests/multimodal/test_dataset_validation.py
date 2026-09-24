from pathlib import Path

import pytest
from training.multimodal.errors import MultimodalTrainingError
from training.multimodal.images import resolve_image_path
from training.multimodal.validation import detect_image_leakage, validate_jsonl_dataset

FIXTURE_ROOT = Path("data/examples/multimodal-mini")


def test_validate_multimodal_fixture_dataset():
    records, report = validate_jsonl_dataset(
        FIXTURE_ROOT,
        dataset_id="multimodal-mini",
        version="1.0.0",
    )
    assert len(records) == 8
    assert report.image_count == 8
    assert report.passed


def test_reject_path_traversal():
    with pytest.raises(MultimodalTrainingError):
        resolve_image_path(FIXTURE_ROOT, "../../secret.png")


def test_detect_image_leakage():
    report = detect_image_leakage({"hash-a"}, {"hash-a"}, set())
    assert not report.passed
    assert "hash-a" in report.overlapping_hashes
