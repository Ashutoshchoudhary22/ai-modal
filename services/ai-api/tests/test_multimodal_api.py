"""Multimodal API tests."""

import pytest
from ai_api.dependencies import reset_dependencies
from ai_api.main import create_app
from ai_api.multimodal.model.mock import DevelopmentMockMultimodalModel
from ai_api.services.multimodal import MultimodalService
from ai_platform_protocol.multimodal import MultimodalRequest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_deps():
    reset_dependencies()
    yield
    reset_dependencies()


def test_multimodal_generate_endpoint():
    app = create_app()
    app.dependency_overrides = {}
    client = TestClient(app)
    response = client.post(
        "/v1/multimodal/generate",
        json={"prompt": "Describe UI", "model": "default"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]
    assert body["provider"] == "development_mock"


def test_multimodal_stream_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/v1/multimodal/generate/stream",
        json={"prompt": "stream", "model": "default"},
    )
    assert response.status_code == 200
    assert "done" in response.text


def test_models_endpoint_includes_multimodal_capabilities():
    app = create_app()
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert "multimodal" in body
    assert body["multimodal"]["capabilities"]["supports_image"] is True


@pytest.mark.asyncio
async def test_multimodal_service_validation_error():
    from ai_api.multimodal.errors import MultimodalError
    from ai_platform_protocol.multimodal import ImageReference
    from ai_platform_shared.config import Settings

    model = DevelopmentMockMultimodalModel(max_images=0)
    service = MultimodalService(
        model=model,
        settings=Settings(multimodal_max_images=0, multimodal_max_pixels=1_000_000),
    )
    with pytest.raises(MultimodalError):
        await service.generate(
            MultimodalRequest(
                images=[
                    ImageReference(
                        id="x",
                        mime_type="image/png",
                        width=1,
                        height=1,
                        byte_size=1,
                        storage_reference="temp://x",
                        sha256="a",
                    )
                ],
                prompt="too many images",
            )
        )
