"""Secure image path resolution and validation for training datasets."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from ai_platform_protocol.multimodal import ImageReference

from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode

_SUPPORTED_MIME = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/webp": "WEBP",
}

_EXTENSION_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@dataclass
class LoadedImage:
    reference: ImageReference
    data: bytes
    width: int
    height: int


def _reject_unsafe_path(path_str: str) -> None:
    if path_str.startswith(("http://", "https://", "ftp://", "file://")):
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Remote image paths are not allowed: {path_str}",
            details={"field": "image", "error_code": "REMOTE_PATH_NOT_ALLOWED"},
        )
    if path_str.startswith("\\\\") or (len(path_str) > 1 and path_str[1] == ":"):
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Absolute image paths are not allowed: {path_str}",
            details={"field": "image", "error_code": "ABSOLUTE_PATH_NOT_ALLOWED"},
        )
    if ".." in Path(path_str).parts:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Path traversal is not allowed: {path_str}",
            details={"field": "image", "error_code": "PATH_TRAVERSAL"},
        )


def resolve_image_path(dataset_root: Path, relative_path: str) -> Path:
    _reject_unsafe_path(relative_path)
    candidate = (dataset_root / relative_path).resolve()
    root = dataset_root.resolve()
    if root not in candidate.parents and candidate != root:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Image path escapes dataset root: {relative_path}",
            details={"field": "image", "error_code": "PATH_OUTSIDE_DATASET_ROOT"},
        )
    return candidate


def validate_and_load_image(
    dataset_root: Path,
    relative_path: str,
    *,
    max_bytes: int = 10_485_760,
    max_width: int = 4096,
    max_height: int = 4096,
    max_pixels: int = 262_144,
) -> LoadedImage:
    try:
        from PIL import Image
    except ImportError as exc:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            "Pillow is required for image validation",
        ) from exc

    image_path = resolve_image_path(dataset_root, relative_path)
    if not image_path.exists():
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Image not found: {relative_path}",
            details={"field": "image", "error_code": "IMAGE_NOT_FOUND"},
        )

    data = image_path.read_bytes()
    if len(data) > max_bytes:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Image exceeds max size: {relative_path}",
            details={"field": "image", "error_code": "IMAGE_TOO_LARGE"},
        )

    suffix = image_path.suffix.lower()
    mime = _EXTENSION_MIME.get(suffix)
    if mime is None:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Unsupported image extension: {relative_path}",
            details={"field": "image", "error_code": "UNSUPPORTED_FORMAT"},
        )

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            actual_format = (img.format or "").upper()
            if actual_format != _SUPPORTED_MIME[mime]:
                raise MultimodalTrainingError(
                    MultimodalTrainingErrorCode.IMAGE_INVALID,
                    f"Image content format mismatch for {relative_path}",
                    details={"field": "image", "error_code": "FORMAT_MISMATCH"},
                )
    except MultimodalTrainingError:
        raise
    except Exception as exc:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Invalid image content: {relative_path}: {exc}",
            details={"field": "image", "error_code": "INVALID_IMAGE"},
        ) from exc

    if width > max_width or height > max_height or width * height > max_pixels:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.IMAGE_INVALID,
            f"Image dimensions exceed limits: {relative_path}",
            details={"field": "image", "error_code": "DIMENSIONS_EXCEEDED"},
        )

    sha256 = hashlib.sha256(data).hexdigest()
    reference = ImageReference(
        id=sha256[:16],
        mime_type=mime,
        width=width,
        height=height,
        byte_size=len(data),
        storage_reference=relative_path,
        sha256=sha256,
    )
    return LoadedImage(reference=reference, data=data, width=width, height=height)
