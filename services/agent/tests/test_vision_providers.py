"""Vision provider tests."""

import pytest
from agent.vision.errors import VisionError
from agent.vision.providers.development_mock import DevelopmentMockVisionProvider
from agent.vision.providers.factory import create_vision_provider
from agent.vision.providers.local import LocalVisionProvider
from agent.vision.providers.proprietary import ProprietaryVisionProvider
from ai_platform_protocol.vision import ImageInput, VisionRequest


@pytest.mark.asyncio
async def test_mock_provider_deterministic():
    provider = DevelopmentMockVisionProvider()
    request = VisionRequest(
        images=[ImageInput(data=b"x", mime_type="image/png", filename="simple-card.png")],
        metadata={"fixture_name": "simple-card"},
    )
    response = await provider.analyze(request)
    assert response.provider == "development_mock"
    assert response.analysis.page_title == "Simple Card"
    assert response.analysis.regions
    data = response.analysis.model_dump()
    assert "regions" in data


@pytest.mark.asyncio
async def test_mock_dashboard_fixture():
    provider = DevelopmentMockVisionProvider()
    response = await provider.analyze(
        VisionRequest(
            images=[ImageInput(data=b"x", mime_type="image/png", filename="dashboard.png")],
            metadata={"fixture_name": "dashboard"},
        )
    )
    assert response.analysis.page_type == "dashboard"


def test_factory_mock():
    provider = create_vision_provider()
    assert provider.provider_id == "development_mock"


@pytest.mark.asyncio
async def test_local_provider_unavailable():
    provider = LocalVisionProvider()
    assert not provider.is_ready()
    with pytest.raises(VisionError):
        await provider.analyze(VisionRequest(images=[]))


@pytest.mark.asyncio
async def test_proprietary_not_implemented():
    provider = ProprietaryVisionProvider()
    with pytest.raises(NotImplementedError):
        await provider.analyze(VisionRequest(images=[]))
