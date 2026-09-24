"""Deterministic mock browser provider for development and tests."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from agent.browser.errors import BrowserError
from agent.browser.observe import build_observation
from agent.browser.policy import validate_url
from agent.config import BrowserSettings, load_browser_settings
from ai_platform_protocol.browser import (
    BrowserElement,
    BrowserErrorCode,
    BrowserObservation,
    BrowserSession,
)

_FIXTURE_ROOT = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "browser"


@dataclass
class _MockPage:
    url: str
    title: str
    visible_text: str
    elements: list[dict]
    screenshot_path: str | None = None
    transitions: dict[str, str] = field(default_factory=dict)


@dataclass
class _MockElementState:
    visible: bool = True
    enabled: bool = True
    value: str = ""
    selected: str | None = None


class MockBrowserSession:
    def __init__(
        self,
        session_id: str,
        run_id: str | None,
        settings: BrowserSettings,
        allowed_domains: list[str] | None,
    ) -> None:
        self.session = BrowserSession(
            session_id=session_id,
            run_id=run_id,
            status="active",
        )
        self._settings = settings
        self._allowed_domains = allowed_domains
        self._pages: dict[str, _MockPage] = {}
        self._history: list[str] = []
        self._history_index = -1
        self._observation_counter = 0
        self._element_state: dict[str, _MockElementState] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        for path in _FIXTURE_ROOT.glob("*/page.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            page = _MockPage(
                url=data["url"],
                title=data.get("title", ""),
                visible_text=data.get("visible_text", ""),
                elements=data.get("elements", []),
                screenshot_path=str(path.parent / "screenshot.png")
                if (path.parent / "screenshot.png").exists()
                else None,
                transitions=data.get("transitions", {}),
            )
            self._pages[page.url] = page
            for el in page.elements:
                self._element_state[el["element_id"]] = _MockElementState(
                    value=el.get("value", ""),
                )

    async def navigate(self, url: str) -> BrowserObservation:
        self._check_navigation_limit()
        validate_url(
            url,
            allowed_domains=self._allowed_domains or self._settings.allowed_domains_list,
            blocked_domains=self._settings.blocked_domains_list,
            allow_localhost=self._settings.allow_localhost,
        )
        if url not in self._pages:
            raise BrowserError(BrowserErrorCode.NAVIGATION_BLOCKED, f"Unknown mock page: {url}")
        self._history = self._history[: self._history_index + 1]
        self._history.append(url)
        self._history_index = len(self._history) - 1
        self.session.navigation_count += 1
        self.session.current_url = url
        page = self._pages[url]
        self.session.title = page.title
        return self._observe_page(page)

    async def observe(self) -> BrowserObservation:
        page = self._current_page()
        return self._observe_page(page)

    async def click(self, element_id: str) -> BrowserObservation:
        self._check_action_limit()
        page = self._current_page()
        el = self._get_element(page, element_id)
        self._validate_element(el, element_id)
        target = page.transitions.get(element_id)
        if target:
            return await self.navigate(target)
        self.session.action_count += 1
        return self._observe_page(page)

    async def fill(self, element_id: str, value: str) -> BrowserObservation:
        self._check_action_limit()
        page = self._current_page()
        el = self._get_element(page, element_id)
        self._validate_element(el, element_id)
        state = self._element_state.setdefault(element_id, _MockElementState())
        state.value = value
        self.session.action_count += 1
        return self._observe_page(page)

    async def type_text(self, element_id: str, value: str) -> BrowserObservation:
        return await self.fill(element_id, value)

    async def select(self, element_id: str, value: str) -> BrowserObservation:
        self._check_action_limit()
        page = self._current_page()
        el = self._get_element(page, element_id)
        self._validate_element(el, element_id)
        state = self._element_state.setdefault(element_id, _MockElementState())
        state.selected = value
        self.session.action_count += 1
        return self._observe_page(page)

    async def press(self, key: str) -> BrowserObservation:
        self._check_action_limit()
        page = self._current_page()
        if key.lower() == "enter":
            for el in page.elements:
                if el.get("role") == "button" and "submit" in (el.get("name") or "").lower():
                    target = page.transitions.get(el["element_id"])
                    if target:
                        return await self.navigate(target)
        self.session.action_count += 1
        return self._observe_page(page)

    async def scroll(self, direction: str, amount: int) -> BrowserObservation:
        self._check_action_limit()
        bounded = min(max(amount, 1), 1000)
        self.session.action_count += 1
        return self._observe_page(self._current_page(), scroll_note=f"{direction}:{bounded}")

    async def wait(self, wait_type: str, value: str | None = None) -> BrowserObservation:
        self._check_action_limit()
        self.session.action_count += 1
        return self._observe_page(self._current_page(), wait_note=f"{wait_type}:{value}")

    async def screenshot(self) -> tuple[BrowserObservation, bytes | None]:
        self._check_screenshot_limit()
        page = self._current_page()
        data = None
        if page.screenshot_path:
            data = Path(page.screenshot_path).read_bytes()
        self.session.screenshot_count += 1
        obs = self._observe_page(page, screenshot_ref=page.screenshot_path)
        return obs, data

    async def back(self) -> BrowserObservation:
        if self._history_index <= 0:
            return self._observe_page(self._current_page())
        self._history_index -= 1
        url = self._history[self._history_index]
        self.session.current_url = url
        return self._observe_page(self._pages[url])

    async def forward(self) -> BrowserObservation:
        if self._history_index >= len(self._history) - 1:
            return self._observe_page(self._current_page())
        self._history_index += 1
        url = self._history[self._history_index]
        self.session.current_url = url
        return self._observe_page(self._pages[url])

    async def reload(self) -> BrowserObservation:
        return self._observe_page(self._current_page())

    async def close(self) -> None:
        self.session.status = "closed"

    def close_sync(self) -> None:
        self.session.status = "closed"

    def _current_page(self) -> _MockPage:
        url = self.session.current_url
        if not url or url not in self._pages:
            raise BrowserError(BrowserErrorCode.BROWSER_SESSION_NOT_FOUND, "No active page")
        return self._pages[url]

    def _observe_page(
        self,
        page: _MockPage,
        *,
        scroll_note: str | None = None,
        wait_note: str | None = None,
        screenshot_ref: str | None = None,
    ) -> BrowserObservation:
        self._observation_counter += 1
        obs_id = f"obs_{self._observation_counter}"
        self.session.current_observation_id = obs_id
        elements: list[BrowserElement] = []
        for raw in page.elements:
            state = self._element_state.get(raw["element_id"], _MockElementState())
            sensitive = raw.get("type") == "password" or raw.get("sensitive", False)
            value = state.value if not sensitive else "[REDACTED]"
            if state.selected:
                value = state.selected
            elements.append(
                BrowserElement(
                    element_id=raw["element_id"],
                    tag=raw.get("tag"),
                    role=raw.get("role"),
                    name=raw.get("name"),
                    text=raw.get("text"),
                    placeholder=raw.get("placeholder"),
                    value=value if value else raw.get("value"),
                    href=raw.get("href"),
                    visible=state.visible and raw.get("visible", True),
                    enabled=state.enabled and raw.get("enabled", True),
                    sensitive=sensitive,
                )
            )
        metadata: dict = {}
        if scroll_note:
            metadata["scroll"] = scroll_note
        if wait_note:
            metadata["wait"] = wait_note
        obs = build_observation(
            observation_id=obs_id,
            url=page.url,
            title=page.title,
            elements=elements,
            visible_text=page.visible_text,
            settings=self._settings,
            screenshot_reference=screenshot_ref,
        )
        if metadata:
            obs.metadata = metadata
        return obs

    def _get_element(self, page: _MockPage, element_id: str) -> dict:
        for el in page.elements:
            if el["element_id"] == element_id:
                return el
        raise BrowserError(
            BrowserErrorCode.ELEMENT_NOT_FOUND,
            f"Element '{element_id}' not found",
        )

    def _validate_element(self, el: dict, element_id: str) -> None:
        state = self._element_state.get(element_id, _MockElementState())
        visible = el.get("visible", True) and state.visible
        enabled = el.get("enabled", True) and state.enabled
        if not visible:
            raise BrowserError(BrowserErrorCode.ELEMENT_NOT_VISIBLE, element_id)
        if not enabled:
            raise BrowserError(BrowserErrorCode.ELEMENT_NOT_ENABLED, element_id)

    def _check_action_limit(self) -> None:
        if self.session.action_count >= self._settings.max_actions:
            raise BrowserError(BrowserErrorCode.ACTION_LIMIT_REACHED, "Action limit reached")

    def _check_navigation_limit(self) -> None:
        if self.session.navigation_count >= self._settings.max_navigations:
            raise BrowserError(
                BrowserErrorCode.NAVIGATION_LIMIT_REACHED,
                "Navigation limit reached",
            )

    def _check_screenshot_limit(self) -> None:
        if self.session.screenshot_count >= self._settings.max_screenshots:
            raise BrowserError(
                BrowserErrorCode.SCREENSHOT_LIMIT_REACHED,
                "Screenshot limit reached",
            )


class DevelopmentMockBrowserProvider:
    provider_id = "development_mock"

    def is_available(self) -> bool:
        return True

    async def create_session(
        self,
        *,
        session_id: str,
        run_id: str | None = None,
        start_url: str | None = None,
        allowed_domains: list[str] | None = None,
    ) -> MockBrowserSession:
        settings = load_browser_settings()
        session = MockBrowserSession(session_id, run_id, settings, allowed_domains)
        if start_url:
            await session.navigate(start_url)
        return session
