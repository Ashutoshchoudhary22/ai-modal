"""Screenshot-to-code API routes."""

from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator
from typing import Any

from ai_platform_protocol.ui import UIValidationMode
from ai_platform_protocol.vision import ImageInput, ScreenshotToCodeRequest, VisionErrorCode
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.loop.events import InMemoryEventSink
from agent.loop.runner import LoopAgentRunner
from agent.screenshot.orchestrator import ScreenshotToCodeOrchestrator
from agent.screenshot.store import get_screenshot_run_store
from agent.vision.errors import VisionError
from agent.vision.providers.factory import create_vision_provider

router = APIRouter()


class ScreenshotToCodeBody(BaseModel):
    workspace_id: str
    prompt: str | None = None
    route: str | None = None
    framework: str | None = None
    responsive: bool = True
    accessibility: bool = True
    validation_mode: str = "build"
    visual_validation_enabled: bool = True
    visual_validation_threshold: float | None = None
    max_visual_iterations: int | None = None
    request_id: str | None = None
    actor_id: str | None = None
    root_path: str | None = None
    image_base64: str | None = None
    image_mime_type: str = "image/png"
    image_filename: str | None = None


def _build_orchestrator(
    runner: LoopAgentRunner | None = None,
    vision_provider: Any | None = None,
) -> ScreenshotToCodeOrchestrator:
    agent_runner = runner or LoopAgentRunner()
    provider = vision_provider or create_vision_provider()
    return ScreenshotToCodeOrchestrator(
        runner=agent_runner,
        vision_provider=provider,
    )


def _vision_http_status(code: VisionErrorCode) -> int:
    if code in {
        VisionErrorCode.INVALID_IMAGE,
        VisionErrorCode.UNSUPPORTED_IMAGE_FORMAT,
        VisionErrorCode.IMAGE_TOO_LARGE,
        VisionErrorCode.IMAGE_DIMENSIONS_EXCEEDED,
    }:
        return 400
    if code == VisionErrorCode.WORKSPACE_ACCESS_DENIED:
        return 403
    return 503


@router.post("/ui/screenshot-to-code")
async def screenshot_to_code(body: ScreenshotToCodeBody) -> dict:
    if not body.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    try:
        image_data = base64.b64decode(body.image_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {exc}") from exc

    request = _to_request(body, image_data)
    orchestrator = _build_orchestrator()
    try:
        result = await orchestrator.generate(request)
    except VisionError as exc:
        raise HTTPException(status_code=_vision_http_status(exc.code), detail=exc.message) from exc
    return result.model_dump()


@router.post("/ui/screenshot-to-code/upload")
async def screenshot_to_code_upload(
    workspace_id: str,
    file: UploadFile,
    prompt: str | None = None,
    route: str | None = None,
    root_path: str | None = None,
    validation_mode: str = "build",
) -> dict:
    data = await file.read()
    mime = file.content_type or "application/octet-stream"
    request = ScreenshotToCodeRequest(
        workspace_id=workspace_id,
        images=[
            ImageInput(data=data, mime_type=mime, filename=file.filename),
        ],
        prompt=prompt,
        route=route,
        root_path=root_path,
        validation_mode=UIValidationMode(validation_mode),
    )
    orchestrator = _build_orchestrator()
    try:
        result = await orchestrator.generate(request)
    except VisionError as exc:
        raise HTTPException(status_code=_vision_http_status(exc.code), detail=exc.message) from exc
    return result.model_dump()


@router.get("/ui/screenshot-to-code/runs/{run_id}")
async def get_screenshot_run(run_id: str) -> dict:
    result = get_screenshot_run_store().get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result.model_dump()


@router.post("/ui/screenshot-to-code/stream")
async def screenshot_to_code_stream(body: ScreenshotToCodeBody) -> StreamingResponse:
    if not body.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    try:
        image_data = base64.b64decode(body.image_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {exc}") from exc

    request = _to_request(body, image_data)
    sink = InMemoryEventSink()
    orchestrator = _build_orchestrator()

    async def event_stream() -> AsyncIterator[str]:
        try:
            result = await orchestrator.generate(request, event_sink=sink)
            payload = {"type": "screenshot.result", "result": result.model_dump()}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        except VisionError as exc:
            err = {"type": "screenshot.error", "error": exc.message, "code": exc.code.value}
            yield f"data: {json.dumps(err)}\n\n"
            return
        for event in sink.list_events(result.run_id):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _to_request(body: ScreenshotToCodeBody, image_data: bytes) -> ScreenshotToCodeRequest:
    return ScreenshotToCodeRequest(
        workspace_id=body.workspace_id,
        images=[
            ImageInput(
                data=image_data,
                mime_type=body.image_mime_type,
                filename=body.image_filename,
            )
        ],
        prompt=body.prompt,
        route=body.route,
        responsive=body.responsive,
        accessibility=body.accessibility,
        validation_mode=UIValidationMode(body.validation_mode),
        visual_validation_enabled=body.visual_validation_enabled,
        visual_validation_threshold=body.visual_validation_threshold,
        max_visual_iterations=body.max_visual_iterations,
        request_id=body.request_id,
        actor_id=body.actor_id,
        root_path=body.root_path,
    )
