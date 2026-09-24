"""Vision pipeline errors."""

from __future__ import annotations

from ai_platform_protocol.vision import VisionErrorCode


class VisionError(Exception):
    def __init__(self, code: VisionErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
