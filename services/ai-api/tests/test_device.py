"""Device detection tests."""

import pytest
from ai_api.providers.device import detect_device, resolve_dtype


def test_detect_device_cpu_when_requested() -> None:
    device = detect_device("cpu")
    assert device.device_type == "cpu"
    assert device.torch_device == "cpu"


def test_detect_device_auto_without_cuda() -> None:
    device = detect_device("auto")
    assert device.device_type in {"cpu", "cuda"}


def test_detect_device_invalid_setting() -> None:
    with pytest.raises(ValueError):
        detect_device("invalid-device")


def test_resolve_dtype_auto_cpu() -> None:
    device = detect_device("cpu")
    assert resolve_dtype("auto", device) == "float32"


def test_resolve_dtype_float16_on_cpu_fails() -> None:
    device = detect_device("cpu")
    with pytest.raises(ValueError):
        resolve_dtype("float16", device)
