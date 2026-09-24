"""Secure image validation and temporary storage."""

from __future__ import annotations

import hashlib
import io
import tempfile
import uuid
from pathlib import Path

from ai_platform_protocol.vision import ImageInput, ImageMetadata, VisionErrorCode
from PIL import Image

from agent.vision.errors import VisionError

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


class ImageValidator:
    def __init__(
        self,
        *,
        max_bytes: int = 10_485_760,
        max_width: int = 4096,
        max_height: int = 4096,
        max_pixels: int = 16_777_216,
    ) -> None:
        self.max_bytes = max_bytes
        self.max_width = max_width
        self.max_height = max_height
        self.max_pixels = max_pixels

    def validate(self, image: ImageInput) -> ImageMetadata:
        if not image.data:
            raise VisionError(VisionErrorCode.INVALID_IMAGE, "Image data is empty")
        if len(image.data) > self.max_bytes:
            raise VisionError(
                VisionErrorCode.IMAGE_TOO_LARGE,
                f"Image exceeds maximum size of {self.max_bytes} bytes",
            )

        mime = self._resolve_mime(image)
        if mime not in _SUPPORTED_MIME:
            raise VisionError(
                VisionErrorCode.UNSUPPORTED_IMAGE_FORMAT,
                f"Unsupported image format: {mime}",
            )

        try:
            with Image.open(io.BytesIO(image.data)) as img:
                img.verify()
            with Image.open(io.BytesIO(image.data)) as img:
                width, height = img.size
                if width > self.max_width or height > self.max_height:
                    raise VisionError(
                        VisionErrorCode.IMAGE_DIMENSIONS_EXCEEDED,
                        f"Image dimensions {width}x{height} exceed limits",
                    )
                if width * height > self.max_pixels:
                    raise VisionError(
                        VisionErrorCode.IMAGE_DIMENSIONS_EXCEEDED,
                        f"Image pixel count {width * height} exceeds limit",
                    )
                actual_format = (img.format or "").upper()
                if actual_format != _SUPPORTED_MIME[mime]:
                    raise VisionError(
                        VisionErrorCode.INVALID_IMAGE,
                        f"Image content format {actual_format} does not match {mime}",
                    )
        except VisionError:
            raise
        except Exception as exc:
            raise VisionError(
                VisionErrorCode.INVALID_IMAGE, f"Corrupted or malformed image: {exc}"
            ) from exc

        image_id = image.image_id or hashlib.sha256(image.data).hexdigest()[:16]
        return ImageMetadata(
            image_id=image_id,
            mime_type=mime,
            width=width,
            height=height,
            size_bytes=len(image.data),
            filename=image.filename,
            viewport=image.viewport,
        )

    def _resolve_mime(self, image: ImageInput) -> str:
        mime = image.mime_type.lower().strip()
        if mime in _SUPPORTED_MIME:
            return mime
        if image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext in _EXTENSION_MIME:
                return _EXTENSION_MIME[ext]
        raise VisionError(
            VisionErrorCode.UNSUPPORTED_IMAGE_FORMAT,
            f"Unsupported or missing MIME type: {image.mime_type}",
        )


class TemporaryImageStore:
    """In-memory/temp storage for uploaded images (not persisted to DB)."""

    def __init__(self) -> None:
        self._root = Path(tempfile.gettempdir()) / "ai-platform-screenshots"
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, image: ImageInput, metadata: ImageMetadata) -> Path:
        ext = Path(metadata.filename or "image.png").suffix or ".png"
        path = self._root / f"{metadata.image_id}-{uuid.uuid4().hex[:8]}{ext}"
        path.write_bytes(image.data)
        return path

    def cleanup(self, path: Path) -> None:
        import contextlib

        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
