"""Shared package tests."""

import pytest
from ai_platform_shared.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.env == "development"
    assert settings.model_provider == "development_mock"


def test_settings_cors_origins_list() -> None:
    settings = Settings(cors_origins="http://a.com, http://b.com")
    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_settings_database_url_mysql() -> None:
    settings = Settings()
    assert settings.database_url.startswith("mysql")
    assert "3306" in settings.database_url


def test_model_provider_normalizes_mock_alias() -> None:
    settings = Settings(model_provider="mock")
    assert settings.model_provider == "development_mock"


def test_production_rejects_mock_provider() -> None:
    settings = Settings(env="production", model_provider="development_mock")
    with pytest.raises(ValueError):
        settings.validate_production_provider()


def test_get_settings_cached() -> None:
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
