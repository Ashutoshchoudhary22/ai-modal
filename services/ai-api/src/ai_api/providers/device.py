"""CUDA/CPU device detection utilities."""

from __future__ import annotations

from dataclasses import dataclass

from ai_platform_protocol.models.provider import DeviceInfo


@dataclass(frozen=True)
class ResolvedDevice:
    device_type: str
    torch_device: str
    device_name: str | None
    cuda_available: bool
    cuda_device_count: int
    dtype: str


def detect_device(device_setting: str = "auto") -> ResolvedDevice:
    requested = device_setting.strip().lower()
    if requested not in {"auto", "cpu"} and not requested.startswith("cuda"):
        raise ValueError(f"Unsupported device setting: {device_setting}")

    try:
        import torch
    except ImportError:
        if requested.startswith("cuda"):
            raise ValueError("CUDA device requested but PyTorch is not installed") from None
        return ResolvedDevice(
            device_type="cpu",
            torch_device="cpu",
            device_name="cpu",
            cuda_available=False,
            cuda_device_count=0,
            dtype="float32",
        )

    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0

    if requested == "cpu":
        return ResolvedDevice(
            device_type="cpu",
            torch_device="cpu",
            device_name="cpu",
            cuda_available=cuda_available,
            cuda_device_count=cuda_device_count,
            dtype="float32",
        )

    if requested.startswith("cuda") or requested == "auto":
        if cuda_available:
            if requested.startswith("cuda:"):
                index = requested.split(":", 1)[1]
                torch_device = f"cuda:{index}"
            else:
                torch_device = "cuda"
            device_name = torch.cuda.get_device_name(0)
            return ResolvedDevice(
                device_type="cuda",
                torch_device=torch_device,
                device_name=device_name,
                cuda_available=True,
                cuda_device_count=cuda_device_count,
                dtype="float16",
            )
        if requested.startswith("cuda"):
            raise ValueError("CUDA device requested but CUDA is unavailable")

    return ResolvedDevice(
        device_type="cpu",
        torch_device="cpu",
        device_name="cpu",
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        dtype="float32",
    )


def resolve_dtype(dtype_setting: str, device: ResolvedDevice) -> str:
    requested = dtype_setting.strip().lower()
    if requested == "auto":
        if device.device_type == "cuda":
            return "float16"
        return "float32"
    if requested not in {"float32", "float16", "bfloat16"}:
        raise ValueError(f"Unsupported dtype setting: {dtype_setting}")
    if requested == "bfloat16" and device.device_type == "cpu":
        raise ValueError("bfloat16 is not supported on CPU for local inference")
    if requested == "float16" and device.device_type == "cpu":
        raise ValueError("float16 is not supported on CPU for local inference")
    return requested


def to_device_info(device: ResolvedDevice) -> DeviceInfo:
    return DeviceInfo(
        device_type=device.device_type,
        device_name=device.device_name,
        cuda_available=device.cuda_available,
        cuda_device_count=device.cuda_device_count,
        dtype=device.dtype,
    )
