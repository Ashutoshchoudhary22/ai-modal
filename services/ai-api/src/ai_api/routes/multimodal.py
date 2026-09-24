"""Multimodal inference API routes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ai_platform_protocol.multimodal import (
    MultimodalErrorCode,
    MultimodalRequest,
    MultimodalResponse,
)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ai_api.dependencies import get_multimodal_service
from ai_api.multimodal.errors import MultimodalError

router = APIRouter(tags=["multimodal"])


def _http_status(code: MultimodalErrorCode) -> int:
    if code in {
        MultimodalErrorCode.MULTIMODAL_INPUT_INVALID,
        MultimodalErrorCode.MULTIMODAL_IMAGE_LIMIT_EXCEEDED,
        MultimodalErrorCode.MULTIMODAL_CONTEXT_LIMIT_EXCEEDED,
        MultimodalErrorCode.MULTIMODAL_CAPABILITY_UNSUPPORTED,
    }:
        return 400
    if code in {
        MultimodalErrorCode.MULTIMODAL_MODEL_NOT_FOUND,
    }:
        return 404
    return 503


@router.post("/multimodal/generate", response_model=MultimodalResponse)
async def multimodal_generate(
    request_body: MultimodalRequest, request: Request
) -> MultimodalResponse:
    service = get_multimodal_service()
    request_id = getattr(request.state, "request_id", None)
    try:
        return await service.generate(request_body, request_id=request_id)
    except MultimodalError as exc:
        raise HTTPException(status_code=_http_status(exc.code), detail=exc.message) from exc


@router.post("/multimodal/generate/stream")
async def multimodal_generate_stream(
    request_body: MultimodalRequest, request: Request
) -> StreamingResponse:
    service = get_multimodal_service()
    request_id = getattr(request.state, "request_id", None)

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for chunk in service.stream(request_body, request_id=request_id):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except MultimodalError as exc:
            err = {"type": "error", "message": exc.message, "code": exc.code.value}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
