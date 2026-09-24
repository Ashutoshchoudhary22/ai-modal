"""UI generation run store."""

from __future__ import annotations

import threading

from ai_platform_protocol.ui import UIGenerationResult


class UIRunStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, UIGenerationResult] = {}

    def save(self, result: UIGenerationResult) -> None:
        with self._lock:
            self._runs[result.run_id] = result

    def get(self, run_id: str) -> UIGenerationResult | None:
        with self._lock:
            return self._runs.get(run_id)


_STORE = UIRunStore()


def get_ui_run_store() -> UIRunStore:
    return _STORE
