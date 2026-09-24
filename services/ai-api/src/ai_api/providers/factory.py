"""Provider factory."""

from __future__ import annotations

from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.providers.base import ModelProvider
from ai_platform_shared.config import Settings

from ai_api.providers.development_mock import DevelopmentMockProvider
from ai_api.providers.errors import ProviderError
from ai_api.providers.local_model import LocalModelProvider
from ai_api.providers.proprietary import ProprietaryModelProvider


def create_provider(settings: Settings) -> ModelProvider:
    settings.validate_production_provider()
    provider = settings.model_provider

    if provider == "development_mock":
        return DevelopmentMockProvider(default_model=settings.default_model)

    if provider == "local":
        return LocalModelProvider(
            model_id=settings.model_id,
            model_path=settings.model_path,
            default_model=settings.default_model,
            device_setting=settings.model_device,
            dtype_setting=settings.model_dtype,
            max_context=settings.model_max_context,
            trust_remote_code=settings.model_trust_remote_code,
            generation_timeout_sec=settings.model_generation_timeout_sec,
        )

    if provider == "proprietary":
        return ProprietaryModelProvider()

    raise ProviderError(
        ProviderErrorCode.MODEL_NOT_CONFIGURED,
        f"Unsupported model provider: {settings.model_provider}",
        status_code=503,
    )
