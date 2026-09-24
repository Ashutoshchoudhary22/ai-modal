"""Inference API routes wired to ModelProvider."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ai_platform_protocol.models.inference import (
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
)
from ai_platform_shared.config import get_settings
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ai_api.dependencies import get_inference_service, get_registry_service

router = APIRouter(tags=["inference"])


@router.get("/models")
async def list_models() -> dict[str, object]:
    settings = get_settings()
    service = get_inference_service()
    provider_status = await service.provider.get_status()
    try:
        registry_models = get_registry_service().list_models(provider=settings.model_provider)
    except Exception:
        registry_models = []
    return {
        "provider": provider_status.provider_id,
        "provider_state": provider_status.state.value,
        "models": [model.model_dump(mode="json") for model in registry_models],
    }


@router.post("/generate", response_model=GenerateResponse)
async def generate(request_body: GenerateRequest, request: Request) -> GenerateResponse:
    service = get_inference_service()
    request_id = getattr(request.state, "request_id", None)
    return await service.generate(request_body, request_id=request_id)


@router.post("/chat", response_model=GenerateResponse)
async def chat(request_body: GenerateRequest, request: Request) -> GenerateResponse:
    return await generate(request_body, request)


@router.post("/generate/stream")
async def generate_stream_legacy(
    request_body: GenerateRequest, request: Request
) -> StreamingResponse:
    return await chat_stream(request_body, request)


@router.post("/chat/stream")
async def chat_stream(request_body: GenerateRequest, request: Request) -> StreamingResponse:
    service = get_inference_service()
    request_id = getattr(request.state, "request_id", None)

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in service.stream(request_body, request_id=request_id):
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/generate/structured", response_model=StructuredGenerateResponse)
async def generate_structured(
    request_body: StructuredGenerateRequest, request: Request
) -> StructuredGenerateResponse:
    service = get_inference_service()
    request_id = getattr(request.state, "request_id", None)
    return await service.generate_structured(request_body, request_id=request_id)


@router.post("/embeddings", response_model=EmbedResponse)
async def embeddings(request_body: EmbedRequest, request: Request) -> EmbedResponse:
    service = get_inference_service()
    request_id = getattr(request.state, "request_id", None)
    return await service.embed(request_body, request_id=request_id)


@router.post("/embed", response_model=EmbedResponse)
async def embed_legacy(request_body: EmbedRequest, request: Request) -> EmbedResponse:
    return await embeddings(request_body, request)
