"""Multimodal request validation."""

from __future__ import annotations

from ai_api.multimodal.context import validate_context_limits
from ai_api.multimodal.errors import MultimodalError
from ai_platform_protocol.multimodal import (
    MultimodalCapabilities,
    MultimodalErrorCode,
    MultimodalRequest,
)


def validate_request(
    request: MultimodalRequest,
    capabilities: MultimodalCapabilities,
    *,
    max_context_tokens: int,
    max_images: int,
    max_pixels: int,
    max_batch_size: int = 8,
) -> None:
    if request.image_count() > 0 and not capabilities.supports_image:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_CAPABILITY_UNSUPPORTED,
            "Provider does not support images",
        )
    if request.image_count() > 1 and not capabilities.supports_multi_image:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_CAPABILITY_UNSUPPORTED,
            "Provider does not support multiple images",
        )
    if request.response_schema and not capabilities.supports_structured_output:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_CAPABILITY_UNSUPPORTED,
            "Provider does not support structured output",
        )
    if request.stream and not capabilities.supports_streaming:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_CAPABILITY_UNSUPPORTED,
            "Provider does not support streaming",
        )
    if request.image_count() > max_batch_size:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_IMAGE_LIMIT_EXCEEDED,
            f"Batch/image limit {max_batch_size} exceeded",
        )
    validate_context_limits(
        request,
        max_context_tokens=max_context_tokens,
        max_images=max_images,
        max_pixels=max_pixels,
    )
