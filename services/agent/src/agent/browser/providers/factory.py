"""Browser provider factory."""

from __future__ import annotations

from agent.browser.providers.base import BrowserProvider
from agent.browser.providers.mock import DevelopmentMockBrowserProvider
from agent.browser.providers.playwright import LocalPlaywrightBrowserProvider
from ai_platform_shared.config import Settings, get_settings


def create_browser_provider(settings: Settings | None = None) -> BrowserProvider:
    cfg = settings or get_settings()
    provider = cfg.browser_provider
    if provider == "development_mock":
        return DevelopmentMockBrowserProvider()
    if provider in {"playwright", "local_playwright"}:
        return LocalPlaywrightBrowserProvider()
    raise ValueError(f"Unknown browser provider: {provider}")
