"""Browser agent run store."""

from __future__ import annotations

import threading

from ai_platform_protocol.browser import BrowserRunResult


class BrowserRunStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, BrowserRunResult] = {}

    def save(self, result: BrowserRunResult) -> None:
        with self._lock:
            self._runs[result.run_id] = result

    def get(self, run_id: str) -> BrowserRunResult | None:
        with self._lock:
            return self._runs.get(run_id)


_STORE = BrowserRunStore()


def get_browser_run_store() -> BrowserRunStore:
    return _STORE
