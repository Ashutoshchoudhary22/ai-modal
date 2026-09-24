import pytest

from training.core.errors import TrainingConfigError
from training.core.hardware import detect_training_hardware, resolve_training_precision


def test_detect_cpu_device():
    hardware = detect_training_hardware("cpu")
    assert hardware.device_type == "cpu"
    assert hardware.torch_device == "cpu"


def test_resolve_fp32_on_cpu():
    hardware = detect_training_hardware("cpu")
    assert resolve_training_precision("fp32", hardware) == "fp32"


def test_reject_fp16_on_cpu():
    hardware = detect_training_hardware("cpu")
    with pytest.raises(TrainingConfigError):
        resolve_training_precision("fp16", hardware)
