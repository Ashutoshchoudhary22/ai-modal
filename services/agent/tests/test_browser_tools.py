"""Browser tool execution tests."""

import pytest
from agent.browser.providers.mock import DevelopmentMockBrowserProvider
from agent.browser.session_registry import get_browser_session_registry
from agent.config import BrowserSettings
from agent.context import ToolExecutionContext
from agent.tools.browser_tools import (
    BrowserClickTool,
    BrowserFillTool,
    BrowserNavigateTool,
    BrowserObserveTool,
    BrowserSelectTool,
)
from ai_platform_protocol.tools import ToolPermission


@pytest.fixture
def browser_context(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = None

    async def setup():
        nonlocal session
        session = await provider.create_session(
            session_id="tool-test",
            start_url="https://example.com/form-page",
            allowed_domains=["example.com"],
        )
        get_browser_session_registry().set("req-1", session)
        return ToolExecutionContext(
            workspace_id="ws",
            workspace_root=tmp_path,
            request_id="req-1",
            permissions={ToolPermission.BROWSER},
        )

    return setup


@pytest.mark.asyncio
async def test_navigate_and_observe(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(session_id="s1", allowed_domains=["example.com"])
    get_browser_session_registry().set("req-1", session)
    ctx = ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req-1",
        permissions={ToolPermission.BROWSER},
    )
    nav = BrowserNavigateTool(BrowserSettings(allowed_domains_list=["example.com"]))
    result = await nav.execute({"url": "https://example.com/simple"}, ctx)
    assert result.success
    assert result.metadata["url"] == "https://example.com/simple"

    observe = BrowserObserveTool()
    obs_result = await observe.execute({}, ctx)
    assert obs_result.success
    assert obs_result.metadata["title"] == "Simple Page"


@pytest.mark.asyncio
async def test_fill_masks_password(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(
        session_id="s2",
        start_url="https://example.com/login",
        allowed_domains=["example.com"],
    )
    get_browser_session_registry().set("req-2", session)
    ctx = ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req-2",
        permissions={ToolPermission.BROWSER},
    )
    fill = BrowserFillTool()
    result = await fill.execute({"element_id": "e2", "value": "secret123"}, ctx)
    assert result.success
    password_el = next(el for el in result.metadata["elements"] if el["element_id"] == "e2")
    assert password_el["value"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_click_disabled_element(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(
        session_id="s3",
        start_url="https://example.com/login",
        allowed_domains=["example.com"],
    )
    get_browser_session_registry().set("req-3", session)
    ctx = ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req-3",
        permissions={ToolPermission.BROWSER},
    )
    click = BrowserClickTool()
    result = await click.execute({"element_id": "e5"}, ctx)
    assert not result.success
    assert result.error_code == "element_not_enabled"


@pytest.mark.asyncio
async def test_stale_observation_reference(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(
        session_id="s4",
        start_url="https://example.com/simple",
        allowed_domains=["example.com"],
    )
    get_browser_session_registry().set("req-4", session)
    ctx = ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req-4",
        permissions={ToolPermission.BROWSER},
    )
    obs = await session.observe()
    old_id = obs.observation_id
    await session.click("e2")
    click = BrowserClickTool()
    result = await click.execute(
        {"element_id": "e1", "observation_id": old_id},
        ctx,
    )
    assert not result.success
    assert result.error_code == "stale_element_reference"


@pytest.mark.asyncio
async def test_select_option(tmp_path):
    provider = DevelopmentMockBrowserProvider()
    session = await provider.create_session(
        session_id="s5",
        start_url="https://example.com/login",
        allowed_domains=["example.com"],
    )
    get_browser_session_registry().set("req-5", session)
    ctx = ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req-5",
        permissions={ToolPermission.BROWSER},
    )
    select = BrowserSelectTool()
    result = await select.execute({"element_id": "e3", "value": "admin"}, ctx)
    assert result.success
