"""Browser provider tests."""

import pytest
from agent.browser.errors import BrowserError
from agent.browser.providers.factory import create_browser_provider
from agent.browser.providers.mock import DevelopmentMockBrowserProvider
from agent.browser.providers.playwright import LocalPlaywrightBrowserProvider
from ai_platform_protocol.browser import BrowserErrorCode


def test_factory_returns_mock_by_default():
    provider = create_browser_provider()
    assert provider.provider_id == "development_mock"
    assert provider.is_available()


@pytest.mark.asyncio
async def test_playwright_provider_unavailable_without_install():
    provider = LocalPlaywrightBrowserProvider()
    if not provider.is_available():
        with pytest.raises(BrowserError) as exc:
            await provider.create_session(session_id="s1")
        assert exc.value.code == BrowserErrorCode.BROWSER_PROVIDER_UNAVAILABLE


@pytest.mark.asyncio
async def test_mock_session_lifecycle():
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(
        session_id="sess-1",
        start_url="https://example.com/simple",
        allowed_domains=["example.com"],
    )
    assert session.session.current_url == "https://example.com/simple"
    assert session.session.title == "Simple Page"
    obs = await session.observe()
    assert obs.observation_id.startswith("obs_")
    assert any(el.element_id == "e2" for el in obs.elements)
    await session.close()
    assert session.session.status == "closed"


@pytest.mark.asyncio
async def test_mock_navigation_limit():
    from agent.config import BrowserSettings

    settings = BrowserSettings(max_navigations=1)
    from agent.browser.providers.mock import MockBrowserSession

    session = MockBrowserSession("s", None, settings, ["example.com"])
    await session.navigate("https://example.com/simple")
    with pytest.raises(BrowserError) as exc:
        await session.navigate("https://example.com/dashboard")
    assert exc.value.code == BrowserErrorCode.NAVIGATION_LIMIT_REACHED
