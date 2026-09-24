from pathlib import Path

from training.datasets.manifest import load_manifest
from training.datasets.pipeline import preprocess_dataset


def test_preprocess_writes_split_files(tmp_path: Path):
    manifest = load_manifest("training/data/manifests/smoke_sft.json")
    processed = preprocess_dataset(
        manifest,
        Path("training/data/manifests/smoke_sft.json"),
        processed_dir=tmp_path / "processed",
    )
    assert processed.train_path.exists()
    assert processed.validation_path.exists()
    assert processed.test_path.exists()
    assert processed.train_count + processed.validation_count + processed.test_count == 10
    assert processed.processed_manifest_path.exists()
