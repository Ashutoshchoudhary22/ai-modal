"""Browser agent API routes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ai_platform_protocol.browser import BrowserErrorCode, BrowserRunRequest
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.browser.errors import BrowserError
from agent.browser.orchestrator import BrowserAgentOrchestrator
from agent.browser.providers.factory import create_browser_provider
from agent.browser.store import get_browser_run_store
from agent.config import load_browser_settings
from agent.loop.events import InMemoryEventSink
from agent.loop.runner import LoopAgentRunner

router = APIRouter()


class BrowserRunBody(BaseModel):
    workspace_id: str
    task: str
    start_url: str | None = None
    policy: str = "browser_agent"
    max_iterations: int | None = None
    request_id: str | None = None
    actor_id: str | None = None
    allowed_domains: list[str] | None = None
    root_path: str | None = None


def _build_orchestrator(runner: LoopAgentRunner | None = None) -> BrowserAgentOrchestrator:
    agent_runner = runner or LoopAgentRunner()
    return BrowserAgentOrchestrator(
        runner=agent_runner,
        provider=create_browser_provider(),
    )


def _browser_http_status(code: BrowserErrorCode) -> int:
    if code in {
        BrowserErrorCode.UNSAFE_URL,
        BrowserErrorCode.DOMAIN_NOT_ALLOWED,
        BrowserErrorCode.INVALID_ACTION,
    }:
        return 400
    if code in {BrowserErrorCode.SSRF_BLOCKED, BrowserErrorCode.NAVIGATION_BLOCKED}:
        return 403
    if code == BrowserErrorCode.BROWSER_SESSION_NOT_FOUND:
        return 404
    return 503


@router.post("/browser/runs")
async def create_browser_run(body: BrowserRunBody) -> dict:
    settings = load_browser_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="Browser agent is disabled")
    request = BrowserRunRequest(
        workspace_id=body.workspace_id,
        task=body.task,
        start_url=body.start_url,
        policy=body.policy,
        max_iterations=body.max_iterations,
        request_id=body.request_id,
        actor_id=body.actor_id,
        allowed_domains=body.allowed_domains,
    )
    orchestrator = _build_orchestrator()
    try:
        result = await orchestrator.run(request, root_path=body.root_path)
    except BrowserError as exc:
        raise HTTPException(status_code=_browser_http_status(exc.code), detail=exc.message) from exc
    return result.model_dump()


@router.get("/browser/runs/{run_id}")
async def get_browser_run(run_id: str) -> dict:
    result = get_browser_run_store().get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Browser run not found")
    return result.model_dump()


@router.post("/browser/runs/{run_id}/cancel")
async def cancel_browser_run(run_id: str) -> dict:
    orchestrator = _build_orchestrator()
    cancelled = await orchestrator.cancel(run_id)
    return {"run_id": run_id, "cancelled": cancelled}


@router.post("/browser/runs/stream")
async def stream_browser_run(body: BrowserRunBody) -> StreamingResponse:
    settings = load_browser_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="Browser agent is disabled")
    sink = InMemoryEventSink()
    request = BrowserRunRequest(
        workspace_id=body.workspace_id,
        task=body.task,
        start_url=body.start_url,
        policy=body.policy,
        max_iterations=body.max_iterations,
        request_id=body.request_id,
        actor_id=body.actor_id,
        allowed_domains=body.allowed_domains,
    )
    orchestrator = _build_orchestrator()

    async def event_stream() -> AsyncIterator[str]:
        try:
            result = await orchestrator.run(request, event_sink=sink, root_path=body.root_path)
            payload = {"type": "browser.result", "result": result.model_dump()}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        except BrowserError as exc:
            err = {"type": "browser.error", "error": exc.message, "code": exc.code.value}
            yield f"data: {json.dumps(err)}\n\n"
            return
        for event in sink.list_events(result.run_id):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
