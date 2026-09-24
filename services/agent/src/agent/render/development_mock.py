"""Mock renderer that returns a reference screenshot for visual comparison tests."""

from __future__ import annotations

import time
from pathlib import Path

from ai_platform_protocol.vision import RenderRequest, RenderResult

_FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "screenshots"


class DevelopmentMockRenderer:
    renderer_id = "development_mock"

    async def render(self, request: RenderRequest) -> RenderResult:
        started = time.perf_counter()
        reference = _FIXTURE_ROOT / "simple-card" / "reference.png"
        if not reference.exists():
            return RenderResult(
                success=False,
                error=f"Mock reference screenshot not found: {reference}",
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        data = reference.read_bytes()
        return RenderResult(
            success=True,
            screenshot_path=str(reference),
            screenshot_bytes=data,
            width=200,
            height=120,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
