"""DevelopmentMockProvider tests."""

import pytest
from ai_api.providers.development_mock import DevelopmentMockProvider
from ai_api.providers.errors import ProviderError
from ai_platform_protocol.models.inference import (
    ChatMessage,
    EmbedRequest,
    GenerateRequest,
    StructuredGenerateRequest,
)


@pytest.fixture
def provider() -> DevelopmentMockProvider:
    return DevelopmentMockProvider(default_model="development-mock-v1")


@pytest.mark.asyncio
async def test_generate(provider: DevelopmentMockProvider) -> None:
    response = await provider.generate(
        GenerateRequest(messages=[ChatMessage(role="user", content="hello")])
    )
    assert response.content.startswith("[development-mock]")
    assert response.usage.total_tokens > 0
    assert response.provider == "development_mock"


@pytest.mark.asyncio
async def test_stream(provider: DevelopmentMockProvider) -> None:
    chunks = [
        chunk
        async for chunk in provider.stream(
            GenerateRequest(messages=[ChatMessage(role="user", content="hello world")])
        )
    ]
    assert any(chunk.type == "chunk" for chunk in chunks)
    assert chunks[-1].type == "done"
    assert chunks[-1].usage is not None


@pytest.mark.asyncio
async def test_structured(provider: DevelopmentMockProvider) -> None:
    response = await provider.generate_structured(
        StructuredGenerateRequest(
            messages=[ChatMessage(role="user", content="list colors")],
            response_schema={
                "type": "object",
                "properties": {"colors": {"type": "array"}},
            },
        )
    )
    assert "colors" in response.parsed


@pytest.mark.asyncio
async def test_embed(provider: DevelopmentMockProvider) -> None:
    response = await provider.embed(EmbedRequest(inputs=["def foo(): pass"]))
    assert len(response.embeddings) == 1
    assert response.dimensions == 2


def test_count_tokens(provider: DevelopmentMockProvider) -> None:
    assert provider.count_tokens("one two three") == 3


@pytest.mark.asyncio
async def test_embed_requires_inputs(provider: DevelopmentMockProvider) -> None:
    with pytest.raises(ProviderError):
        await provider.embed(EmbedRequest(inputs=[]))


@pytest.mark.asyncio
async def test_vision_unavailable(provider: DevelopmentMockProvider) -> None:
    from ai_platform_protocol.models.inference import VisionRequest

    with pytest.raises(ProviderError):
        await provider.vision(VisionRequest(messages=[ChatMessage(role="user", content="x")]))
