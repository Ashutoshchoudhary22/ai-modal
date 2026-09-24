"""Per-run browser session registry."""

from __future__ import annotations

import contextlib
import threading

from agent.browser.providers.base import BrowserProviderSession


class BrowserSessionRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, BrowserProviderSession] = {}

    def set(self, key: str, session: BrowserProviderSession) -> None:
        with self._lock:
            self._sessions[key] = session

    def get(self, key: str) -> BrowserProviderSession | None:
        with self._lock:
            return self._sessions.get(key)

    def pop(self, key: str) -> BrowserProviderSession | None:
        with self._lock:
            return self._sessions.pop(key, None)

    def close_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            with contextlib.suppress(Exception):
                session.close_sync()


_REGISTRY = BrowserSessionRegistry()


def get_browser_session_registry() -> BrowserSessionRegistry:
    return _REGISTRY
