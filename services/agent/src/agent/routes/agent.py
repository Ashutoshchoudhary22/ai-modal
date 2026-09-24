"""Agent run API routes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from ai_platform_protocol.agent import AgentRunConfig
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.config import load_agent_settings
from agent.loop.errors import AgentExecutionError
from agent.loop.events import InMemoryEventSink
from agent.loop.model_client import StructuredModelClient
from agent.loop.runner import LoopAgentRunner
from agent.loop.store import get_run_store

router = APIRouter()


class CreateAgentRunBody(BaseModel):
    workspace_id: str
    task: str
    policy: str | None = None
    max_iterations: int | None = None
    model_id: str = "default"
    request_id: str | None = None
    actor_id: str | None = None
    root_path: str | None = None
    validation_mode: str = "none"


def _build_runner(model_client: Any | None = None) -> LoopAgentRunner:
    if model_client is not None:
        return LoopAgentRunner(model_client=model_client)
    try:
        from ai_api.providers.factory import create_provider
        from ai_platform_shared.config import get_settings

        provider = create_provider(get_settings())
        client = StructuredModelClient(provider, model_id=get_settings().default_model)
        return LoopAgentRunner(model_client=client)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Model provider unavailable; install ai-platform-ai-api",
        ) from exc


@router.post("/agent/runs")
async def create_agent_run(body: CreateAgentRunBody) -> dict:
    settings = load_agent_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="Agent loop is disabled")
    config = AgentRunConfig(
        workspace_id=body.workspace_id,
        workspace_root=body.root_path,
        task=body.task,
        policy=body.policy or settings.default_policy,
        max_iterations=body.max_iterations or settings.max_iterations,
        model_id=body.model_id,
        request_id=body.request_id,
        actor_id=body.actor_id,
        validation_mode=body.validation_mode,
    )
    runner = _build_runner()
    try:
        result = await runner.run(config, root_path=body.root_path)
    except AgentExecutionError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return result.model_dump()


@router.get("/agent/runs/{run_id}")
async def get_agent_run(run_id: str) -> dict:
    summary = get_run_store().summary(run_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary.model_dump()


@router.post("/agent/runs/{run_id}/cancel")
async def cancel_agent_run(run_id: str) -> dict:
    runner = _build_runner()
    cancelled = await runner.cancel(run_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "cancelled": True}


@router.post("/agent/runs/stream")
async def stream_agent_run(body: CreateAgentRunBody) -> StreamingResponse:
    settings = load_agent_settings()
    if not settings.enabled:
        raise HTTPException(status_code=503, detail="Agent loop is disabled")
    config = AgentRunConfig(
        workspace_id=body.workspace_id,
        workspace_root=body.root_path,
        task=body.task,
        policy=body.policy or settings.default_policy,
        max_iterations=body.max_iterations or settings.max_iterations,
        model_id=body.model_id,
        request_id=body.request_id,
        actor_id=body.actor_id,
        validation_mode=body.validation_mode,
    )
    sink = InMemoryEventSink()
    runner = _build_runner()

    async def event_stream() -> AsyncIterator[str]:
        try:
            result = await runner.run(config, event_sink=sink, root_path=body.root_path)
            payload = {"type": "run.result", "result": result.model_dump()}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        except AgentExecutionError as exc:
            err_payload = {"type": "run.error", "error": exc.message, "code": exc.code.value}
            yield f"data: {json.dumps(err_payload)}\n\n"
            return
        for event in sink.list_events(result.run_id):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
