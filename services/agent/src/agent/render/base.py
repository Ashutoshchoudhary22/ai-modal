"""UI rendering protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_platform_protocol.vision import RenderRequest, RenderResult


@runtime_checkable
class UIRenderer(Protocol):
    @property
    def renderer_id(self) -> str: ...

    async def render(self, request: RenderRequest) -> RenderResult: ...
