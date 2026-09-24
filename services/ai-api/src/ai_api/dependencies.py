"""Application dependencies and singletons."""

from __future__ import annotations

from functools import lru_cache

from ai_platform_shared.config import get_settings

from ai_api.multimodal.factory import create_multimodal_model
from ai_api.providers.factory import create_provider
from ai_api.services.inference import InferenceService
from ai_api.services.multimodal import MultimodalService
from ai_api.services.registry import RegistryService


@lru_cache
def get_inference_service() -> InferenceService:
    settings = get_settings()
    provider = create_provider(settings)
    return InferenceService(provider)


@lru_cache
def get_registry_service() -> RegistryService:
    return RegistryService()


@lru_cache
def get_multimodal_service() -> MultimodalService:
    settings = get_settings()
    model = create_multimodal_model(settings)
    return MultimodalService(model=model, settings=settings)


def reset_dependencies() -> None:
    get_inference_service.cache_clear()
    get_registry_service.cache_clear()
    get_multimodal_service.cache_clear()
    get_settings.cache_clear()
