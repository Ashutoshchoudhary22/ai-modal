import pytest

from training.core.config import LoRAConfig
from training.core.errors import TrainingConfigError
from training.core.trainer import _validate_lora_targets


def test_lora_config_requires_target_modules_when_enabled():
    config = LoRAConfig(enabled=True, target_modules=[])
    assert config.enabled is True


def test_validate_lora_targets_detects_missing_modules():
    class DummyModule:
        def named_modules(self):
            return [("layer", object())]

    with pytest.raises(TrainingConfigError):
        _validate_lora_targets(DummyModule(), ["missing_module"])
