"""Local browser renderer — scoped to screenshot capture only (not Phase 9 agent)."""

from __future__ import annotations

from ai_platform_protocol.vision import RenderRequest, RenderResult


class LocalBrowserRenderer:
    """Narrow renderer for build → navigate → screenshot → cleanup."""

    renderer_id = "local_browser"

    async def render(self, request: RenderRequest) -> RenderResult:
        return RenderResult(
            success=False,
            error=(
                "Local browser renderer requires optional playwright dependency. "
                "Use AI_PLATFORM_UI_RENDERER=development_mock for tests."
            ),
        )
