from pathlib import Path

import pytest
import yaml


@pytest.mark.integration
def test_smoke_training_pipeline(tmp_path: Path):
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    pytest.importorskip("datasets")

    from training.core.config import load_training_config
    from training.core.trainer import run_training

    source_config = load_training_config("models/configs/smoke_test.yaml")
    config_dict = source_config.model_dump(mode="json")
    config_dict["output"]["dir"] = str(tmp_path / "smoke-output")

    config_path = tmp_path / "smoke_config.yaml"
    config_path.write_text(yaml.safe_dump(config_dict), encoding="utf-8")

    final_dir = run_training(config_path)
    assert final_dir.exists()
    assert any(final_dir.iterdir())
    assert (tmp_path / "smoke-output" / "experiment.json").exists()
    assert (tmp_path / "smoke-output" / "training_metadata.json").exists()
