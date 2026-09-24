"""Browser agent errors."""

from __future__ import annotations

from ai_platform_protocol.browser import BrowserErrorCode


class BrowserError(Exception):
    def __init__(self, code: BrowserErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
