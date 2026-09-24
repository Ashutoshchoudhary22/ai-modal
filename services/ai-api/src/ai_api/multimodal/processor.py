"""Image preprocessing for multimodal models."""

from __future__ import annotations

import hashlib
import io

from ai_api.multimodal.errors import MultimodalError
from ai_platform_protocol.multimodal import (
    ImageProcessingMetadata,
    MultimodalErrorCode,
    ProcessedImage,
)
from PIL import Image


class ImageProcessor:
    def __init__(
        self,
        *,
        target_size: int = 224,
        max_pixels: int = 16_777_216,
    ) -> None:
        self._target_size = target_size
        self._max_pixels = max_pixels

    def process(
        self,
        *,
        image_id: str,
        mime_type: str,
        data: bytes,
        width: int,
        height: int,
    ) -> ProcessedImage:
        if width * height > self._max_pixels:
            raise MultimodalError(
                MultimodalErrorCode.IMAGE_PROCESSING_FAILED,
                f"Image pixels {width * height} exceed limit",
            )
        try:
            with Image.open(io.BytesIO(data)) as img:
                img = img.convert("RGB")
                processed = self._resize_preserve_aspect(img)
                proc_w, proc_h = processed.size
        except Exception as exc:
            raise MultimodalError(
                MultimodalErrorCode.IMAGE_PROCESSING_FAILED,
                f"Failed to process image: {exc}",
            ) from exc

        scale = min(self._target_size / width, self._target_size / height, 1.0)
        return ProcessedImage(
            image_id=image_id,
            mime_type=mime_type,
            metadata=ImageProcessingMetadata(
                original_width=width,
                original_height=height,
                processed_width=proc_w,
                processed_height=proc_h,
                scale=scale,
            ),
            tensor_shape=[1, 3, proc_h, proc_w],
            data_reference=hashlib.sha256(data).hexdigest(),
        )

    def _resize_preserve_aspect(self, img: Image.Image) -> Image.Image:
        width, height = img.size
        scale = min(self._target_size / width, self._target_size / height, 1.0)
        new_w = max(1, int(width * scale))
        new_h = max(1, int(height * scale))
        return img.resize((new_w, new_h), Image.Resampling.BILINEAR)
