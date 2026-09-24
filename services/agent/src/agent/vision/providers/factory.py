"""Vision provider factory."""

from __future__ import annotations

from agent.vision.providers.base import VisionProvider
from agent.vision.providers.development_mock import DevelopmentMockVisionProvider
from agent.vision.providers.local import LocalVisionProvider
from agent.vision.providers.proprietary import ProprietaryVisionProvider
from ai_platform_shared.config import Settings, get_settings


def create_vision_provider(settings: Settings | None = None) -> VisionProvider:
    cfg = settings or get_settings()
    if cfg.vision_use_multimodal:
        from agent.vision.providers.multimodal import MultimodalVisionProvider
        from ai_api.multimodal.factory import create_multimodal_model

        return MultimodalVisionProvider(create_multimodal_model(cfg))
    provider = cfg.vision_provider
    if provider == "development_mock":
        return DevelopmentMockVisionProvider()
    if provider == "local":
        return LocalVisionProvider(model_ref=cfg.vision_model, device=cfg.model_device)
    if provider == "proprietary":
        return ProprietaryVisionProvider()
    raise ValueError(f"Unknown vision provider: {provider}")
