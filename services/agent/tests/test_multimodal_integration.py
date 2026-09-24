"""Phase 10 agent integration tests."""

from pathlib import Path

import pytest
from agent.multimodal.browser_adapter import browser_observation_to_request
from agent.multimodal.references import image_reference_from_input
from agent.vision.image import ImageValidator
from agent.vision.providers.multimodal import MultimodalVisionProvider
from ai_api.multimodal.model.mock import DevelopmentMockMultimodalModel
from ai_platform_protocol.browser import BrowserElement, BrowserObservation
from ai_platform_protocol.vision import ImageInput

FIXTURES = Path(__file__).parent / "fixtures" / "screenshots" / "simple-card"


@pytest.mark.asyncio
async def test_multimodal_vision_provider_analyze():
    data = (FIXTURES / "reference.png").read_bytes()
    provider = MultimodalVisionProvider(DevelopmentMockMultimodalModel())
    response = await provider.analyze(
        __import__("ai_platform_protocol.vision", fromlist=["VisionRequest"]).VisionRequest(
            images=[ImageInput(data=data, mime_type="image/png", filename="reference.png")],
            prompt="Analyze screenshot",
        )
    )
    assert response.analysis.page_title
    assert response.provider == "multimodal"


def test_browser_observation_adapter():
    obs = BrowserObservation(
        observation_id="obs_1",
        url="https://example.com",
        title="Example",
        elements=[
            BrowserElement(element_id="e1", role="button", name="Submit"),
        ],
        visible_text="Submit",
    )
    request = browser_observation_to_request(obs, task="Click submit")
    assert request.metadata["source"] == "browser_observation"
    assert "Submit" in request.resolved_messages()[0].text_parts()[1]


def test_image_reference_has_no_filesystem_path():
    data = (FIXTURES / "reference.png").read_bytes()
    validator = ImageValidator()
    metadata = validator.validate(ImageInput(data=data, mime_type="image/png"))
    ref = image_reference_from_input(ImageInput(data=data, mime_type="image/png"), metadata)
    assert ref.storage_reference.startswith("temp://")
    assert "/" not in ref.storage_reference.replace("temp://", "")
