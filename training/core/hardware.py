"""Hardware detection for training."""

from __future__ import annotations

from dataclasses import dataclass

from training.core.errors import TrainingConfigError


@dataclass(frozen=True)
class TrainingHardwareInfo:
    device_type: str
    torch_device: str
    device_name: str | None
    cuda_available: bool
    cuda_device_count: int
    total_vram_gb: float | None
    precision_supported: dict[str, bool]


def detect_training_hardware(device_setting: str = "auto") -> TrainingHardwareInfo:
    requested = device_setting.strip().lower()
    if requested not in {"auto", "cpu"} and not requested.startswith("cuda"):
        raise TrainingConfigError(f"Unsupported device setting: {device_setting}")

    try:
        import torch
    except ImportError as exc:
        if requested.startswith("cuda"):
            raise TrainingConfigError("CUDA requested but PyTorch is not installed") from exc
        return TrainingHardwareInfo(
            device_type="cpu",
            torch_device="cpu",
            device_name="cpu",
            cuda_available=False,
            cuda_device_count=0,
            total_vram_gb=None,
            precision_supported={"fp32": True, "fp16": False, "bf16": False},
        )

    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0
    total_vram_gb = None
    device_name = "cpu"
    torch_device = "cpu"
    device_type = "cpu"

    if requested == "cpu":
        pass
    elif requested.startswith("cuda") or requested == "auto":
        if cuda_available:
            device_type = "cuda"
            torch_device = requested if requested.startswith("cuda:") else "cuda"
            device_name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            total_vram_gb = round(props.total_memory / (1024**3), 2)
        elif requested.startswith("cuda"):
            raise TrainingConfigError("CUDA requested but CUDA is unavailable")
    else:
        raise TrainingConfigError(f"Unsupported device setting: {device_setting}")

    precision_supported = {"fp32": True, "fp16": False, "bf16": False}
    if device_type == "cuda":
        precision_supported["fp16"] = True
        precision_supported["bf16"] = torch.cuda.is_bf16_supported()

    return TrainingHardwareInfo(
        device_type=device_type,
        torch_device=torch_device,
        device_name=device_name,
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        total_vram_gb=total_vram_gb,
        precision_supported=precision_supported,
    )


def resolve_training_precision(precision: str, hardware: TrainingHardwareInfo) -> str:
    requested = precision.strip().lower()
    if requested == "auto":
        if hardware.device_type == "cuda" and hardware.precision_supported["bf16"]:
            return "bf16"
        if hardware.device_type == "cuda":
            return "fp16"
        return "fp32"
    if requested not in {"fp32", "fp16", "bf16"}:
        raise TrainingConfigError(f"Unsupported precision: {precision}")
    if not hardware.precision_supported.get(requested, False):
        raise TrainingConfigError(
            f"Precision {requested} is not supported on {hardware.device_type} "
            f"({hardware.device_name})"
        )
    return requested
