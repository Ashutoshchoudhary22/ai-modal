"""Browser interaction tools — Phase 9."""

from __future__ import annotations

from typing import Any

from agent.browser.errors import BrowserError
from agent.browser.policy import validate_url
from agent.browser.session_registry import get_browser_session_registry
from agent.config import BrowserSettings, load_browser_settings
from agent.context import ToolExecutionContext
from agent.errors import ToolErrorCode
from agent.tools.base import BaseTool
from ai_platform_protocol.browser import BrowserErrorCode
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult

_BROWSER_PERMISSIONS = [ToolPermission.BROWSER]


class BrowserToolBase(BaseTool):
    def __init__(self, settings: BrowserSettings | None = None) -> None:
        self._settings = settings or load_browser_settings()

    def _session(self, context: ToolExecutionContext):
        session = get_browser_session_registry().get(context.request_id)
        if session is None:
            raise BrowserError(
                BrowserErrorCode.BROWSER_SESSION_NOT_FOUND,
                "No browser session for this run",
            )
        return session

    def _check_observation(self, session, observation_id: str | None) -> None:
        if observation_id is None:
            return
        current = session.session.current_observation_id
        if current and observation_id != current:
            raise BrowserError(
                BrowserErrorCode.STALE_ELEMENT_REFERENCE,
                f"Observation '{observation_id}' is stale; current is '{current}'",
            )

    def _observation_result(self, obs) -> ToolResult:
        return self._ok(obs.model_dump())

    def _browser_fail(self, exc: BrowserError) -> ToolResult:
        return ToolResult(
            success=False,
            error=exc.message,
            error_code=exc.code.value,
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        if not self._settings.enabled:
            return ToolResult(
                success=False,
                error="Browser tools are disabled",
                error_code=ToolErrorCode.TOOLS_DISABLED.value,
            )
        try:
            return await self._execute_browser(arguments, context)
        except BrowserError as exc:
            return self._browser_fail(exc)

    async def _execute_browser(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        raise NotImplementedError


class BrowserNavigateTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.navigate",
        description="Navigate the browser to a URL",
        parameters_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "url")
        url = validate_url(
            arguments["url"],
            allowed_domains=self._settings.allowed_domains_list,
            blocked_domains=self._settings.blocked_domains_list,
            allow_localhost=self._settings.allow_localhost,
        )
        session = self._session(context)
        obs = await session.navigate(url)
        return self._observation_result(obs)


class BrowserObserveTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.observe",
        description="Observe the current browser page state",
        parameters_schema={"type": "object", "properties": {}},
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        session = self._session(context)
        obs = await session.observe()
        return self._observation_result(obs)


class BrowserClickTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.click",
        description="Click a page element by element_id",
        parameters_schema={
            "type": "object",
            "properties": {
                "element_id": {"type": "string"},
                "observation_id": {"type": "string"},
            },
            "required": ["element_id"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "element_id")
        session = self._session(context)
        self._check_observation(session, arguments.get("observation_id"))
        obs = await session.click(arguments["element_id"])
        return self._observation_result(obs)


class BrowserFillTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.fill",
        description="Fill a form field by element_id",
        parameters_schema={
            "type": "object",
            "properties": {
                "element_id": {"type": "string"},
                "value": {"type": "string"},
                "observation_id": {"type": "string"},
            },
            "required": ["element_id", "value"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "element_id", "value")
        session = self._session(context)
        self._check_observation(session, arguments.get("observation_id"))
        obs = await session.fill(arguments["element_id"], arguments["value"])
        return self._observation_result(obs)


class BrowserTypeTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.type",
        description="Type text into an element by element_id",
        parameters_schema={
            "type": "object",
            "properties": {
                "element_id": {"type": "string"},
                "value": {"type": "string"},
                "observation_id": {"type": "string"},
            },
            "required": ["element_id", "value"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "element_id", "value")
        session = self._session(context)
        self._check_observation(session, arguments.get("observation_id"))
        obs = await session.type_text(arguments["element_id"], arguments["value"])
        return self._observation_result(obs)


class BrowserSelectTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.select",
        description="Select an option in a native select element",
        parameters_schema={
            "type": "object",
            "properties": {
                "element_id": {"type": "string"},
                "value": {"type": "string"},
                "observation_id": {"type": "string"},
            },
            "required": ["element_id", "value"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "element_id", "value")
        session = self._session(context)
        self._check_observation(session, arguments.get("observation_id"))
        obs = await session.select(arguments["element_id"], arguments["value"])
        return self._observation_result(obs)


class BrowserScrollTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.scroll",
        description="Scroll the page in a direction",
        parameters_schema={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                "amount": {"type": "integer"},
            },
            "required": ["direction"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "direction")
        amount = int(arguments.get("amount", 300))
        session = self._session(context)
        obs = await session.scroll(arguments["direction"], amount)
        return self._observation_result(obs)


class BrowserPressTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.press",
        description="Press a keyboard key",
        parameters_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "enum": [
                        "Enter",
                        "Escape",
                        "Tab",
                        "ArrowUp",
                        "ArrowDown",
                        "Backspace",
                    ],
                }
            },
            "required": ["key"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "key")
        session = self._session(context)
        obs = await session.press(arguments["key"])
        return self._observation_result(obs)


class BrowserWaitTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.wait",
        description="Wait for navigation, text, or timeout",
        parameters_schema={
            "type": "object",
            "properties": {
                "wait_type": {
                    "type": "string",
                    "enum": ["navigation", "text", "timeout"],
                },
                "value": {"type": "string"},
            },
            "required": ["wait_type"],
        },
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        self._require_args(arguments, "wait_type")
        session = self._session(context)
        obs = await session.wait(arguments["wait_type"], arguments.get("value"))
        return self._observation_result(obs)


class BrowserScreenshotTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.screenshot",
        description="Capture a screenshot of the current page",
        parameters_schema={"type": "object", "properties": {}},
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        session = self._session(context)
        obs, _data = await session.screenshot()
        return self._observation_result(obs)


class BrowserBackTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.back",
        description="Navigate back in browser history",
        parameters_schema={"type": "object", "properties": {}},
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        session = self._session(context)
        obs = await session.back()
        return self._observation_result(obs)


class BrowserForwardTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.forward",
        description="Navigate forward in browser history",
        parameters_schema={"type": "object", "properties": {}},
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        session = self._session(context)
        obs = await session.forward()
        return self._observation_result(obs)


class BrowserReloadTool(BrowserToolBase):
    definition = ToolDefinition(
        name="browser.reload",
        description="Reload the current page",
        parameters_schema={"type": "object", "properties": {}},
        permissions=_BROWSER_PERMISSIONS,
    )

    async def _execute_browser(
        self, arguments: dict[str, Any], context: ToolExecutionContext
    ) -> ToolResult:
        session = self._session(context)
        obs = await session.reload()
        return self._observation_result(obs)


def all_browser_tools(settings: BrowserSettings | None = None) -> list[BaseTool]:
    cfg = settings or load_browser_settings()
    return [
        BrowserNavigateTool(cfg),
        BrowserObserveTool(cfg),
        BrowserClickTool(cfg),
        BrowserFillTool(cfg),
        BrowserTypeTool(cfg),
        BrowserSelectTool(cfg),
        BrowserScrollTool(cfg),
        BrowserPressTool(cfg),
        BrowserWaitTool(cfg),
        BrowserScreenshotTool(cfg),
        BrowserBackTool(cfg),
        BrowserForwardTool(cfg),
        BrowserReloadTool(cfg),
    ]
