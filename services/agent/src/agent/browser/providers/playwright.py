"""Local Playwright browser provider — optional dependency."""

from __future__ import annotations

from agent.browser.errors import BrowserError
from ai_platform_protocol.browser import BrowserErrorCode


class LocalPlaywrightBrowserProvider:
    provider_id = "playwright"

    def is_available(self) -> bool:
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            return False

    async def create_session(self, **kwargs):  # type: ignore[no-untyped-def]
        raise BrowserError(
            BrowserErrorCode.BROWSER_PROVIDER_UNAVAILABLE,
            "Playwright browser provider is not fully configured. "
            "Use AI_PLATFORM_BROWSER_PROVIDER=development_mock for tests.",
        )
