"""Development mock multimodal model with modular pipeline."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from ai_api.multimodal.context import account_context, estimate_text_tokens
from ai_api.multimodal.encoder.mock import DevelopmentMockVisionEncoder
from ai_api.multimodal.errors import MultimodalError
from ai_api.multimodal.fusion.mock import DevelopmentMockFusion
from ai_api.multimodal.processor import ImageProcessor
from ai_api.multimodal.projector.mock import DevelopmentMockProjector
from ai_platform_protocol.multimodal import (
    ImageContent,
    ImageReference,
    MultimodalCapabilities,
    MultimodalErrorCode,
    MultimodalRequest,
    MultimodalResponse,
    MultimodalStreamChunk,
    MultimodalUsage,
    ProcessedImage,
    TextContent,
)


class DevelopmentMockMultimodalModel:
    provider_id = "development_mock"

    def __init__(
        self,
        *,
        model_id: str = "development-mock-multimodal-v1",
        max_context_tokens: int = 8192,
        max_images: int = 4,
        max_pixels: int = 16_777_216,
    ) -> None:
        self._model_id = model_id
        self._max_context_tokens = max_context_tokens
        self._max_images = max_images
        self._max_pixels = max_pixels
        self._processor = ImageProcessor(max_pixels=max_pixels)
        self._encoder = DevelopmentMockVisionEncoder()
        self._projector = DevelopmentMockProjector()
        self._fusion = DevelopmentMockFusion()

    @property
    def model_id(self) -> str:
        return self._model_id

    def is_available(self) -> bool:
        return True

    def capabilities(self) -> MultimodalCapabilities:
        return MultimodalCapabilities(
            supports_text=True,
            supports_image=True,
            supports_multi_image=True,
            supports_streaming=True,
            supports_structured_output=True,
            max_context_tokens=self._max_context_tokens,
            max_images=self._max_images,
            max_image_pixels=self._max_pixels,
            embedding_dimension=16,
            modalities=["text", "image", "multimodal"],
        )

    async def generate(self, request: MultimodalRequest) -> MultimodalResponse:
        if request.response_schema:
            return await self.generate_structured(request)
        fused, budget, started = await self._run_pipeline(request)
        text = self._build_text_response(request, fused)
        usage = MultimodalUsage(
            text_input_tokens=budget.text_tokens,
            visual_input_tokens=budget.visual_tokens,
            total_input_units=budget.total_context_cost,
            output_tokens=estimate_text_tokens(text),
            image_count=budget.image_count,
            processing_time_ms=started,
        )
        return MultimodalResponse(
            id=f"mm_{uuid.uuid4().hex[:12]}",
            model=request.model if request.model != "default" else self._model_id,
            content=text,
            finish_reason="stop",
            usage=usage,
            provider=self.provider_id,
            metadata={"pipeline": "modular_mock", "fusion": fused.get("strategy")},
        )

    async def generate_structured(self, request: MultimodalRequest) -> MultimodalResponse:
        fused, budget, started = await self._run_pipeline(request)
        parsed = self._build_structured_response(request, fused)
        usage = MultimodalUsage(
            text_input_tokens=budget.text_tokens,
            visual_input_tokens=budget.visual_tokens,
            total_input_units=budget.total_context_cost,
            output_tokens=estimate_text_tokens(json.dumps(parsed)),
            image_count=budget.image_count,
            processing_time_ms=started,
        )
        return MultimodalResponse(
            id=f"mm_{uuid.uuid4().hex[:12]}",
            model=request.model if request.model != "default" else self._model_id,
            parsed=parsed,
            finish_reason="stop",
            usage=usage,
            provider=self.provider_id,
            metadata={"pipeline": "modular_mock", "structured": True},
        )

    async def stream(self, request: MultimodalRequest) -> AsyncIterator[MultimodalStreamChunk]:
        response = await self.generate(request)
        content = response.content or json.dumps(response.parsed or {})
        for token in content.split():
            await asyncio.sleep(0)
            yield MultimodalStreamChunk(
                type="chunk",
                content=token + " ",
                provider=self.provider_id,
            )
        yield MultimodalStreamChunk(
            type="done",
            usage=response.usage,
            finish_reason="stop",
            provider=self.provider_id,
        )

    def count_tokens(self, text: str) -> int:
        return estimate_text_tokens(text)

    async def _run_pipeline(self, request: MultimodalRequest):
        import time

        started = time.perf_counter()
        budget = account_context(
            request,
            max_context_tokens=self._max_context_tokens,
            max_images=self._max_images,
            max_pixels=self._max_pixels,
        )
        if not budget.within_limit:
            if budget.image_count > self._max_images:
                raise MultimodalError(
                    MultimodalErrorCode.MULTIMODAL_IMAGE_LIMIT_EXCEEDED,
                    "Too many images",
                )
            raise MultimodalError(
                MultimodalErrorCode.MULTIMODAL_CONTEXT_LIMIT_EXCEEDED,
                "Context limit exceeded",
            )

        processed = self._collect_processed_images(request)
        vision_output = await self._encoder.encode(processed)
        projected = await self._projector.project(vision_output)
        text_inputs = self._collect_text(request)
        fused = await self._fusion.fuse(text_inputs, projected)
        elapsed = int((time.perf_counter() - started) * 1000)
        return fused, budget, elapsed

    def _collect_processed_images(self, request: MultimodalRequest) -> list[ProcessedImage]:
        processed: list[ProcessedImage] = []
        for message in request.resolved_messages():
            for part in message.content:
                if isinstance(part, ImageContent):
                    processed.append(self._process_reference(part.image))
        for image in request.images:
            processed.append(self._process_reference(image))
        return processed

    def _process_reference(self, image: ImageReference) -> ProcessedImage:
        import io

        from PIL import Image

        width = max(1, min(image.width, 512))
        height = max(1, min(image.height, 512))
        buffer = io.BytesIO()
        Image.new("RGB", (width, height), color=(64, 128, 192)).save(buffer, format="PNG")
        return self._processor.process(
            image_id=image.id,
            mime_type=image.mime_type,
            data=buffer.getvalue(),
            width=image.width,
            height=image.height,
        )

    def _collect_text(self, request: MultimodalRequest) -> list[str]:
        texts: list[str] = []
        for message in request.resolved_messages():
            for part in message.content:
                if isinstance(part, TextContent):
                    texts.append(part.text)
        return texts

    def _build_text_response(self, request: MultimodalRequest, fused: dict) -> str:
        prompt = " ".join(fused.get("text_inputs", [])) or request.prompt or ""
        image_count = fused.get("image_count", 0) or len(
            [t for t in fused.get("visual_tokens", []) if t.startswith("[IMAGE_")]
        )
        return (
            f"[development-mock-multimodal] images={image_count} "
            f"visual_tokens={fused.get('visual_token_count', 0)} "
            f"prompt={prompt[:200]}"
        )

    def _build_structured_response(self, request: MultimodalRequest, fused: dict) -> dict:
        schema_name = (request.response_schema or {}).get("title", "response")
        prompt = " ".join(fused.get("text_inputs", [])) or request.prompt or ""
        if (
            "visual" in prompt.lower()
            or "screenshot" in prompt.lower()
            or fused.get("visual_token_count", 0)
        ):
            return {
                "page_title": prompt[:80] or "Mock Page",
                "page_type": "page",
                "layout": {"type": "single-column"},
                "elements": [
                    {
                        "element_type": "header",
                        "label": "Header",
                        "confidence": "observed",
                    }
                ],
                "design_tokens": {"primary_color": "#2563eb"},
                "schema": schema_name,
            }
        if (request.metadata or {}).get("decision_schema"):
            return {
                "type": "final",
                "message": f"Mock multimodal decision for: {prompt[:120]}",
            }
        return {
            "summary": prompt[:200],
            "image_count": len(fused.get("visual_tokens", [])),
            "schema": schema_name,
        }
