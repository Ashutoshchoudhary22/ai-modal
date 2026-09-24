"""Multimodal provider factory."""

from __future__ import annotations

from ai_api.multimodal.errors import MultimodalError
from ai_api.multimodal.model.base import MultimodalModel
from ai_api.multimodal.model.local import LocalMultimodalModel
from ai_api.multimodal.model.mock import DevelopmentMockMultimodalModel
from ai_api.multimodal.model.proprietary import ProprietaryMultimodalModel
from ai_platform_protocol.multimodal import MultimodalErrorCode
from ai_platform_shared.config import Settings, get_settings


def create_multimodal_model(settings: Settings | None = None) -> MultimodalModel:
    cfg = settings or get_settings()
    provider = cfg.multimodal_provider
    model_id = cfg.multimodal_model or "development-mock-multimodal-v1"

    if provider == "development_mock":
        return DevelopmentMockMultimodalModel(
            model_id=model_id,
            max_context_tokens=cfg.multimodal_max_context_tokens,
            max_images=cfg.multimodal_max_images,
            max_pixels=cfg.multimodal_max_pixels,
        )
    if provider == "local":
        model = LocalMultimodalModel(model_id=model_id)
        if not model.is_available():
            raise MultimodalError(
                MultimodalErrorCode.MULTIMODAL_PROVIDER_UNAVAILABLE,
                "Local multimodal provider dependencies are not installed",
            )
        return model
    if provider == "proprietary":
        return ProprietaryMultimodalModel(model_id=model_id)
    raise MultimodalError(
        MultimodalErrorCode.MULTIMODAL_PROVIDER_UNAVAILABLE,
        f"Unknown multimodal provider: {provider}",
    )
