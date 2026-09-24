"""Vision provider backed by MultimodalModel — Phase 10 integration."""

from __future__ import annotations

import json
import time

from agent.multimodal.references import image_reference_from_input
from agent.vision.image import ImageValidator, TemporaryImageStore
from ai_platform_protocol.multimodal import MultimodalMessage, MultimodalRequest, TextContent
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


class MultimodalVisionProvider:
    provider_id = "multimodal"
    provider_name = "Multimodal Vision Provider"

    def __init__(self, multimodal_model) -> None:
        self._model = multimodal_model
        self._validator = ImageValidator()
        self._store = TemporaryImageStore()

    def is_ready(self) -> bool:
        return self._model.is_available()

    async def analyze(self, request: VisionRequest) -> VisionResponse:
        started = time.perf_counter()
        if not request.images:
            raise ValueError("At least one image is required")

        content: list = []
        if request.prompt:
            content.append(TextContent(text=request.prompt))
        for image in request.images:
            metadata = self._validator.validate(image)
            reference = image_reference_from_input(image, metadata, self._store)
            from ai_platform_protocol.multimodal import ImageContent

            content.append(ImageContent(image=reference))

        mm_request = MultimodalRequest(
            model=self._model.model_id,
            messages=[MultimodalMessage(role="user", content=content)],
            response_schema={
                "title": "VisualAnalysis",
                "type": "object",
                "properties": {
                    "page_title": {"type": "string"},
                    "page_type": {"type": "string"},
                    "layout": {"type": "object"},
                    "elements": {"type": "array"},
                },
            },
            metadata={"source": "vision_provider"},
        )
        response = await self._model.generate_structured(mm_request)
        analysis = self._to_visual_analysis(response.parsed or {}, request)
        duration = int((time.perf_counter() - started) * 1000)
        return VisionResponse(
            analysis=analysis,
            provider=self.provider_id,
            model=self._model.model_id,
            duration_ms=duration,
            metadata={"multimodal": True},
        )

    def _to_visual_analysis(self, parsed: dict, request: VisionRequest) -> VisualAnalysis:
        if parsed.get("page_title"):
            elements = []
            for item in parsed.get("elements", []):
                elements.append(
                    VisualElement(
                        element_type=item.get("element_type", "section"),
                        label=item.get("label", "Element"),
                        region=VisualRegion(x=0, y=0, width=1, height=0.1),
                        confidence=ConfidenceLevel.OBSERVED,
                    )
                )
            layout = parsed.get("layout") or {"type": "single-column"}
            tokens = parsed.get("design_tokens") or {"primary_color": "#2563eb"}
            return VisualAnalysis(
                page_title=parsed.get("page_title", "Page"),
                page_type=parsed.get("page_type", "page"),
                layout=LayoutSpec.model_validate(layout)
                if isinstance(layout, dict)
                else LayoutSpec(type="single-column"),
                elements=elements,
                design_tokens=DesignTokens.model_validate(tokens)
                if isinstance(tokens, dict)
                else DesignTokens(),
            )
        prompt = request.prompt or "Screenshot"
        return VisualAnalysis(
            page_title=prompt,
            page_type="page",
            layout=LayoutSpec(type="single-column"),
            elements=[
                VisualElement(
                    element_type="section",
                    label="Content",
                    region=VisualRegion(x=0, y=0, width=1, height=1),
                    confidence=ConfidenceLevel.INFERRED,
                )
            ],
            design_tokens=DesignTokens(primary_color="#2563eb"),
            metadata={"fallback": True, "parsed": json.dumps(parsed)[:200]},
        )
