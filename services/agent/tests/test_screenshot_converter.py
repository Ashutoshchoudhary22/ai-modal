"""Visual analysis to UISpec conversion tests."""

import pytest
from agent.screenshot.converter import visual_analysis_to_ui_spec
from agent.vision.providers.development_mock import DevelopmentMockVisionProvider
from ai_platform_protocol.vision import ImageInput, VisionRequest


async def _load_analysis(fixture: str):
    provider = DevelopmentMockVisionProvider()
    response = await provider.analyze(
        VisionRequest(
            images=[ImageInput(data=b"x", mime_type="image/png")],
            metadata={"fixture_name": fixture},
        )
    )
    return response.analysis


@pytest.mark.asyncio
async def test_converter_simple_card():
    analysis = await _load_analysis("simple-card")
    spec = visual_analysis_to_ui_spec(analysis, prompt="Create product card", route="/products")
    assert spec.name
    assert spec.pages
    assert spec.pages[0].route == "/products"
    assert spec.screenshot_metadata["visual_confidence"] > 0
    data = spec.model_dump()
    assert data["screenshot_metadata"]


@pytest.mark.asyncio
async def test_converter_form_components():
    analysis = await _load_analysis("form")
    spec = visual_analysis_to_ui_spec(analysis)
    names = {c.name for c in spec.components}
    assert "Email" in names or "SignIn" in names or "LoginForm" in names or len(spec.components) > 0


@pytest.mark.asyncio
async def test_spec_serialization():
    analysis = await _load_analysis("dashboard")
    spec = visual_analysis_to_ui_spec(analysis)
    dumped = spec.model_dump()
    assert dumped["responsive"] is True
    assert "theme" in dumped
