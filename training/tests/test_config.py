
from training.core.config import load_training_config
from training.datasets.manifest import load_manifest


def test_load_smoke_manifest():
    manifest = load_manifest("training/data/manifests/smoke_sft.json")
    assert manifest.dataset.name == "smoke-sft"
    assert manifest.source.license
    assert manifest.dataset.synthetic is True


def test_load_smoke_training_config():
    config = load_training_config("models/configs/smoke_test.yaml")
    assert config.experiment.smoke_test is True
    assert config.hardware.device == "cpu"
    assert config.lora.enabled is False


def test_registry_requires_fields():
    config = load_training_config("models/configs/smoke_test.yaml")
    assert config.registry.enabled is False
