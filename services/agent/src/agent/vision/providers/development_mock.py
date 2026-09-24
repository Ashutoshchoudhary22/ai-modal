"""Deterministic mock vision provider for development and tests."""

from __future__ import annotations

import json
import time
from pathlib import Path

from ai_platform_protocol.vision import (
    ConfidenceLevel,
    DesignTokens,
    LayoutSpec,
    VisionRequest,
    VisionResponse,
    VisualAnalysis,
    VisualElement,
    VisualRegion,
)

_FIXTURE_ROOT = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "screenshots"


class DevelopmentMockVisionProvider:
    provider_id = "development_mock"
    provider_name = "Development Mock Vision Provider"

    def is_ready(self) -> bool:
        return True

    async def analyze(self, request: VisionRequest) -> VisionResponse:
        started = time.perf_counter()
        analysis = self._resolve_analysis(request)
        duration = int((time.perf_counter() - started) * 1000)
        return VisionResponse(
            analysis=analysis,
            provider=self.provider_id,
            model="development-mock-vision-v1",
            duration_ms=duration,
            metadata={"mock": True},
        )

    def _resolve_analysis(self, request: VisionRequest) -> VisualAnalysis:
        fixture_name = request.metadata.get("fixture_name")
        if fixture_name:
            return self._load_fixture(str(fixture_name))

        filename = ""
        if request.images:
            filename = (request.images[0].filename or "").lower()

        if "dashboard" in filename:
            return self._load_fixture("dashboard")
        if "form" in filename:
            return self._load_fixture("form")
        if "landing" in filename:
            return self._load_fixture("landing-page")
        if "card" in filename:
            return self._load_fixture("simple-card")

        return self._default_analysis(request)

    def _load_fixture(self, name: str) -> VisualAnalysis:
        path = _FIXTURE_ROOT / name / "analysis.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return VisualAnalysis.model_validate(data)
        return self._default_analysis(None)

    def _default_analysis(self, request: VisionRequest | None) -> VisualAnalysis:
        prompt = (request.prompt if request else None) or "Generated UI"
        return VisualAnalysis(
            page_title=prompt,
            page_type="page",
            regions=[
                VisualElement(
                    element_type="header",
                    label="Header",
                    region=VisualRegion(x=0, y=0, width=1, height=0.1, label="header"),
                    confidence=ConfidenceLevel.OBSERVED,
                ),
                VisualElement(
                    element_type="section",
                    label="Main Content",
                    region=VisualRegion(x=0, y=0.1, width=1, height=0.8, label="content"),
                    confidence=ConfidenceLevel.OBSERVED,
                    children=[
                        VisualElement(
                            element_type="card",
                            label="Card",
                            text="Content card",
                            confidence=ConfidenceLevel.OBSERVED,
                        )
                    ],
                ),
                VisualElement(
                    element_type="footer",
                    label="Footer",
                    region=VisualRegion(x=0, y=0.9, width=1, height=0.1, label="footer"),
                    confidence=ConfidenceLevel.OBSERVED,
                ),
            ],
            layout=LayoutSpec(
                direction="column",
                layout_type="flex",
                alignment="stretch",
                confidence=ConfidenceLevel.INFERRED,
            ),
            design_tokens=DesignTokens(
                colors={
                    "primary": "#2563eb",
                    "background": "#ffffff",
                    "text": "#111827",
                    "border": "#e5e7eb",
                },
                typography={"body": "16px", "heading": "24px"},
                spacing={"md": "16px", "lg": "24px"},
            ),
            responsive_hints=["stack on mobile", "sidebar collapses on tablet"],
            accessibility_notes=["use semantic headings", "label form inputs"],
            overall_confidence=0.9,
            provider=self.provider_id,
            model="development-mock-vision-v1",
        )
