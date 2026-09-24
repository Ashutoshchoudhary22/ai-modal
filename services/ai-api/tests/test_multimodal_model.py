"""Multimodal model pipeline tests."""

import pytest
from ai_api.multimodal.context import account_context
from ai_api.multimodal.encoder.mock import DevelopmentMockVisionEncoder
from ai_api.multimodal.factory import create_multimodal_model
from ai_api.multimodal.fusion.mock import DevelopmentMockFusion
from ai_api.multimodal.model.mock import DevelopmentMockMultimodalModel
from ai_api.multimodal.processor import ImageProcessor
from ai_api.multimodal.projector.mock import DevelopmentMockProjector
from ai_platform_protocol.multimodal import (
    ImageContent,
    ImageReference,
    MultimodalMessage,
    MultimodalRequest,
    TextContent,
)
from ai_platform_shared.config import Settings


def _image_ref(image_id: str = "img1") -> ImageReference:
    return ImageReference(
        id=image_id,
        mime_type="image/png",
        width=128,
        height=64,
        byte_size=2048,
        storage_reference=f"temp://{image_id}",
        sha256=f"{image_id}-hash",
    )


@pytest.mark.asyncio
async def test_mock_pipeline_end_to_end():
    processor = ImageProcessor()
    encoder = DevelopmentMockVisionEncoder()
    projector = DevelopmentMockProjector()
    fusion = DevelopmentMockFusion()

    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 32)).save(buf, format="PNG")
    processed = processor.process(
        image_id="img1",
        mime_type="image/png",
        data=buf.getvalue(),
        width=64,
        height=32,
    )
    vision = await encoder.encode([processed])
    projected = await projector.project(vision)
    fused = await fusion.fuse(["compare screenshots"], projected)
    assert fused["visual_token_count"] > 0


@pytest.mark.asyncio
async def test_mock_multimodal_generate_text_only():
    model = DevelopmentMockMultimodalModel()
    response = await model.generate(MultimodalRequest(prompt="Hello"))
    assert response.content
    assert "development-mock-multimodal" in response.content


@pytest.mark.asyncio
async def test_mock_multimodal_generate_with_image():
    model = DevelopmentMockMultimodalModel()
    request = MultimodalRequest(
        messages=[
            MultimodalMessage(
                role="user",
                content=[
                    TextContent(text="Analyze screenshot"),
                    ImageContent(image=_image_ref()),
                ],
            )
        ]
    )
    response = await model.generate(request)
    assert response.usage.image_count == 1
    assert response.content


@pytest.mark.asyncio
async def test_mock_multimodal_structured_output():
    model = DevelopmentMockMultimodalModel()
    response = await model.generate_structured(
        MultimodalRequest(
            prompt="screenshot layout",
            response_schema={"title": "VisualAnalysis"},
        )
    )
    assert response.parsed
    assert response.parsed.get("page_title")


@pytest.mark.asyncio
async def test_mock_multimodal_streaming():
    model = DevelopmentMockMultimodalModel()
    chunks = []
    async for chunk in model.stream(MultimodalRequest(prompt="stream test")):
        chunks.append(chunk)
    assert chunks[-1].type == "done"


def test_context_accounting():
    request = MultimodalRequest(
        messages=[
            MultimodalMessage(
                role="user",
                content=[TextContent(text="one two three"), ImageContent(image=_image_ref())],
            )
        ]
    )
    budget = account_context(request, max_context_tokens=1000, max_images=4, max_pixels=1_000_000)
    assert budget.text_tokens >= 3
    assert budget.image_count == 1
    assert budget.within_limit


def test_factory_development_mock():
    model = create_multimodal_model(Settings(multimodal_provider="development_mock"))
    assert model.provider_id == "development_mock"
    assert model.is_available()
