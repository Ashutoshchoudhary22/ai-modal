from pathlib import Path

import pytest
import yaml


@pytest.fixture
def smoke_config_path(tmp_path: Path) -> Path:
    source = Path("training/configs/multimodal/sft.yaml")
    config = yaml.safe_load(source.read_text(encoding="utf-8"))
    config["output"]["dir"] = str(tmp_path / "output")
    config["dataset"]["path"] = "data/examples/multimodal-mini"
    config_path = tmp_path / "smoke.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_dry_run(smoke_config_path: Path):
    pytest.importorskip("torch")
    from training.multimodal.trainer import run_multimodal_training

    output = run_multimodal_training(smoke_config_path, dry_run=True)
    assert (output / "training_plan.txt").exists()


def test_one_step_training_and_checkpoint(smoke_config_path: Path):
    pytest.importorskip("torch")
    from training.multimodal.trainer import run_multimodal_training

    final_dir = run_multimodal_training(smoke_config_path)
    assert final_dir.exists()
    assert (final_dir / "model.pt").exists()
    assert (final_dir / "checkpoint_metadata.json").exists()
    assert (final_dir.parent / "experiment.json").exists()
    assert (final_dir.parent / "reproducibility.json").exists()


def test_resume_training(smoke_config_path: Path):
    pytest.importorskip("torch")
    from training.multimodal.trainer import run_multimodal_training

    first_dir = run_multimodal_training(smoke_config_path)
    checkpoint = first_dir.parent / "checkpoint-000002"
    if not checkpoint.exists():
        checkpoint = first_dir
    resumed_dir = run_multimodal_training(
        smoke_config_path,
        resume_from_checkpoint=checkpoint,
    )
    assert resumed_dir.exists()


def test_lora_reduces_trainable_parameters():
    pytest.importorskip("torch")
    from training.multimodal.config import (
        DatasetSection,
        ExperimentSection,
        ModelSection,
        MultimodalTrainingConfig,
        OutputSection,
        PeftSection,
    )
    from training.multimodal.model import build_model
    from training.multimodal.peft import apply_lora
    from training.multimodal.tokenizer import CharTokenizer

    config = MultimodalTrainingConfig(
        experiment=ExperimentSection(name="lora"),
        dataset=DatasetSection(path="data/examples/multimodal-mini"),
        output=OutputSection(dir="."),
        model=ModelSection(),
        peft=PeftSection(enabled=True, target_modules=["lm_head"]),
    )
    tokenizer = CharTokenizer()
    tokenizer.build_vocab(["hello", "world"])
    model = build_model(config.model, tokenizer, image_size=16)
    full_params = model.trainable_parameters().trainable_parameters
    apply_lora(model, config.peft)
    lora_params = model.trainable_parameters().trainable_parameters
    assert lora_params < full_params


def test_gradient_accumulation_configured(smoke_config_path: Path):
    config = yaml.safe_load(smoke_config_path.read_text(encoding="utf-8"))
    assert config["training"]["gradient_accumulation_steps"] == 2
