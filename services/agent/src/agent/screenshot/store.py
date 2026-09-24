"""Screenshot-to-code run store."""

from __future__ import annotations

import threading

from ai_platform_protocol.vision import ScreenshotToCodeResult


class ScreenshotRunStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, ScreenshotToCodeResult] = {}

    def save(self, result: ScreenshotToCodeResult) -> None:
        with self._lock:
            self._runs[result.run_id] = result

    def get(self, run_id: str) -> ScreenshotToCodeResult | None:
        with self._lock:
            return self._runs.get(run_id)


_STORE = ScreenshotRunStore()


def get_screenshot_run_store() -> ScreenshotRunStore:
    return _STORE
