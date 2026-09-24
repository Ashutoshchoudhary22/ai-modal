"""Code completion API routes."""

from __future__ import annotations

from ai_platform_protocol.completion import CompletionRequest, CompletionResponse
from fastapi import APIRouter, HTTPException, Request

from ai_api.completion.service import CompletionServiceError
from ai_api.dependencies import get_completion_service

router = APIRouter()


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(
    request_body: CompletionRequest,
    request: Request,
) -> CompletionResponse:
    service = get_completion_service()
    if request_body.request_id is None:
        request_body.request_id = getattr(request.state, "request_id", None)
    try:
        return await service.complete(request_body)
    except CompletionServiceError as exc:
        status = 400
        if exc.code in {"COMPLETION_PROVIDER_UNAVAILABLE"}:
            status = 503
        elif exc.code in {"COMPLETION_SENSITIVE_FILE", "COMPLETION_CONTEXT_TOO_LARGE"}:
            status = 403
        raise HTTPException(
            status_code=status, detail={"code": exc.code, "message": exc.message}
        ) from exc
