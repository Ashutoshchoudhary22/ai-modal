"""Multimodal context and token accounting."""

from __future__ import annotations

from ai_api.multimodal.errors import MultimodalError
from ai_platform_protocol.multimodal import ContextBudget, MultimodalErrorCode, MultimodalRequest


def estimate_text_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()))


def account_context(
    request: MultimodalRequest,
    *,
    max_context_tokens: int,
    max_images: int,
    max_pixels: int,
) -> ContextBudget:
    text_tokens = 0
    image_count = 0
    image_pixels = 0
    visual_tokens = 0

    for message in request.resolved_messages():
        for part in message.content:
            if part.type == "text":
                text_tokens += estimate_text_tokens(part.text)
            elif part.type == "image":
                image_count += 1
                pixels = part.image.width * part.image.height
                image_pixels += pixels
                grid = max(1, (part.image.width // 32) * (part.image.height // 32))
                visual_tokens += grid

    for image in request.images:
        image_count += 1
        pixels = image.width * image.height
        image_pixels += pixels
        grid = max(1, (image.width // 32) * (image.height // 32))
        visual_tokens += grid

    total = text_tokens + visual_tokens
    within = (
        image_count <= max_images and image_pixels <= max_pixels and total <= max_context_tokens
    )
    return ContextBudget(
        text_tokens=text_tokens,
        visual_tokens=visual_tokens,
        image_count=image_count,
        image_pixels=image_pixels,
        total_context_cost=total,
        within_limit=within,
    )


def validate_context_limits(
    request: MultimodalRequest,
    *,
    max_context_tokens: int,
    max_images: int,
    max_pixels: int,
) -> ContextBudget:
    budget = account_context(
        request,
        max_context_tokens=max_context_tokens,
        max_images=max_images,
        max_pixels=max_pixels,
    )
    if budget.image_count > max_images:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_IMAGE_LIMIT_EXCEEDED,
            f"Image count {budget.image_count} exceeds limit {max_images}",
        )
    if budget.image_pixels > max_pixels:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_INPUT_INVALID,
            f"Total image pixels {budget.image_pixels} exceed limit {max_pixels}",
        )
    if budget.total_context_cost > max_context_tokens:
        raise MultimodalError(
            MultimodalErrorCode.MULTIMODAL_CONTEXT_LIMIT_EXCEEDED,
            f"Context cost {budget.total_context_cost} exceeds limit {max_context_tokens}",
        )
    return budget
