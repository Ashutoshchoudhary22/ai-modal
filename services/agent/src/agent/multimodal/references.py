"""Build secure image references from validated image inputs."""

from __future__ import annotations

import hashlib

from agent.vision.image import TemporaryImageStore
from ai_platform_protocol.multimodal import ImageReference
from ai_platform_protocol.vision import ImageInput, ImageMetadata


def image_reference_from_input(
    image: ImageInput,
    metadata: ImageMetadata,
    store: TemporaryImageStore | None = None,
) -> ImageReference:
    temp_store = store or TemporaryImageStore()
    temp_store.save(image, metadata)
    return ImageReference(
        id=metadata.image_id,
        mime_type=metadata.mime_type,
        width=metadata.width,
        height=metadata.height,
        byte_size=metadata.size_bytes,
        storage_reference=f"temp://{metadata.image_id}",
        sha256=hashlib.sha256(image.data).hexdigest(),
    )
