"""Provider factory tests."""

import pytest
from ai_api.providers.development_mock import DevelopmentMockProvider
from ai_api.providers.errors import ProviderError
from ai_api.providers.factory import create_provider
from ai_api.providers.local_model import LocalModelProvider
from ai_api.providers.proprietary import ProprietaryModelProvider
from ai_platform_shared.config import Settings


def test_factory_returns_mock_provider() -> None:
    provider = create_provider(Settings(model_provider="mock"))
    assert isinstance(provider, DevelopmentMockProvider)


def test_factory_returns_local_provider() -> None:
    provider = create_provider(Settings(model_provider="local", model_id="sshleifer/tiny-gpt2"))
    assert isinstance(provider, LocalModelProvider)


def test_factory_returns_proprietary_placeholder() -> None:
    provider = create_provider(Settings(model_provider="proprietary"))
    assert isinstance(provider, ProprietaryModelProvider)


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderError):
        create_provider(Settings(model_provider="unknown"))


def test_factory_rejects_mock_in_production() -> None:
    with pytest.raises(ValueError):
        create_provider(Settings(env="production", model_provider="development_mock"))
