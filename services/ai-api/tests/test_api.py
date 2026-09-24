"""AI API service tests."""

import pytest
from ai_api.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_ready(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "development_mock"
    assert data["provider_state"] in {"ready", "configured", "unavailable"}


@pytest.mark.asyncio
async def test_meta(client: AsyncClient) -> None:
    response = await client.get("/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert "development_mock" in data["providers"]


@pytest.mark.asyncio
async def test_models(client: AsyncClient) -> None:
    response = await client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "development_mock"


@pytest.mark.asyncio
async def test_generate(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/generate",
        json={
            "messages": [{"role": "user", "content": "Explain Python decorators"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "development-mock" in data["content"]
    assert data["usage"]["total_tokens"] > 0
    assert data["provider"] == "development_mock"


@pytest.mark.asyncio
async def test_chat(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/chat",
        json={"prompt": "Say hello", "system_prompt": "You are helpful"},
    )
    assert response.status_code == 200
    assert "development-mock" in response.json()["content"]


@pytest.mark.asyncio
async def test_embeddings(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/embeddings",
        json={"inputs": ["def foo(): pass", "class Bar: pass"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["embeddings"]) == 2
    assert data["dimensions"] == 2


@pytest.mark.asyncio
async def test_embed_legacy(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/embed",
        json={"inputs": ["hello"]},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_stream(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/chat/stream",
        json={"messages": [{"role": "user", "content": "stream this"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "data:" in body
    assert "chunk" in body


@pytest.mark.asyncio
async def test_structured_generate(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/generate/structured",
        json={
            "messages": [{"role": "user", "content": "Return JSON"}],
            "response_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
        },
    )
    assert response.status_code == 200
    assert "name" in response.json()["parsed"]
