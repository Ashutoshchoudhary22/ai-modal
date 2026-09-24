"""UI generation API routes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from ai_platform_protocol.ui import UIGenerationRequest, UIValidationMode
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.config import load_ui_settings
from agent.loop.events import InMemoryEventSink
from agent.loop.model_client import StructuredModelClient
from agent.loop.runner import LoopAgentRunner
from agent.ui.generator import UIGenerator
from agent.ui.store import get_ui_run_store

router = APIRouter()


class GenerateUIBody(BaseModel):
    workspace_id: str
    prompt: str
    target: str = "page"
    route: str | None = None
    framework: str | None = None
    styling_system: str | None = None
    responsive: bool = True
    accessibility: bool = True
    validation_mode: str = "build"
    request_id: str | None = None
    actor_id: str | None = None
    root_path: str | None = None


def _build_generator(model_client: Any | None = None) -> UIGenerator:
    if model_client is not None:
        return UIGenerator(runner=LoopAgentRunner(model_client=model_client))
    try:
        from ai_api.providers.factory import create_provider
        from ai_platform_shared.config import get_settings

        provider = create_provider(get_settings())
        client = StructuredModelClient(provider, model_id=get_settings().default_model)
        return UIGenerator(runner=LoopAgentRunner(model_client=client))
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Model provider unavailable; install ai-platform-ai-api",
        ) from exc


def _to_request(body: GenerateUIBody) -> UIGenerationRequest:
    settings = load_ui_settings()
    return UIGenerationRequest(
        workspace_id=body.workspace_id,
        prompt=body.prompt,
        target=body.target,
        route=body.route,
        responsive=body.responsive,
        accessibility=body.accessibility,
        validation_mode=UIValidationMode(body.validation_mode or settings.default_validation),
        request_id=body.request_id,
        actor_id=body.actor_id,
        root_path=body.root_path,
    )


@router.post("/ui/generate")
async def generate_ui(body: GenerateUIBody) -> dict:
    settings = load_ui_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="UI generation is disabled")
    generator = _build_generator()
    try:
        result = await generator.generate(_to_request(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


@router.get("/ui/runs/{run_id}")
async def get_ui_run(run_id: str) -> dict:
    result = get_ui_run_store().get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="UI run not found")
    return result.model_dump()


@router.post("/ui/generate/stream")
async def stream_ui_generate(body: GenerateUIBody) -> StreamingResponse:
    settings = load_ui_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="UI generation is disabled")
    sink = InMemoryEventSink()
    generator = _build_generator()

    async def event_stream() -> AsyncIterator[str]:
        try:
            result = await generator.generate(_to_request(body), event_sink=sink)
            payload = {"type": "ui.result", "result": result.model_dump()}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'ui.error', 'error': str(exc)})}\n\n"
            return
        for event in sink.list_events(result.run_id):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
