"""Vision provider factory."""

from __future__ import annotations

from agent.vision.providers.base import VisionProvider
from agent.vision.providers.development_mock import DevelopmentMockVisionProvider
from agent.vision.providers.local import LocalVisionProvider
from agent.vision.providers.proprietary import ProprietaryVisionProvider
from ai_platform_shared.config import Settings, get_settings


def create_vision_provider(settings: Settings | None = None) -> VisionProvider:
    cfg = settings or get_settings()
    provider = cfg.vision_provider
    if provider == "development_mock":
        return DevelopmentMockVisionProvider()
    if provider == "local":
        return LocalVisionProvider(model_ref=cfg.vision_model, device=cfg.model_device)
    if provider == "proprietary":
        return ProprietaryVisionProvider()
    raise ValueError(f"Unknown vision provider: {provider}")
