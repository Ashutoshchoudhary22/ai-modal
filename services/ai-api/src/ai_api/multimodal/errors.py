"""Multimodal inference errors."""

from __future__ import annotations

from ai_platform_protocol.multimodal import MultimodalErrorCode


class MultimodalError(Exception):
    def __init__(self, code: MultimodalErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
