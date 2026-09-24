"""Tool discovery and execution routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.registry import ToolRegistry
from agent.services.workspace_resolver import build_context

router = APIRouter()
_registry = ToolRegistry()


class ExecuteToolBody(BaseModel):
    workspace_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    root_path: str | None = None
    request_id: str | None = None
    actor_id: str | None = None


@router.get("/tools")
async def list_tools() -> dict:
    tools = _registry.list()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
                "permissions": [p.value for p in tool.permissions],
                "timeout_sec": tool.timeout_sec,
            }
            for tool in tools
        ]
    }


@router.post("/tools/execute")
async def execute_tool(body: ExecuteToolBody) -> dict:
    try:
        context = build_context(
            workspace_id=body.workspace_id,
            root_path=body.root_path,
            request_id=body.request_id,
            actor_id=body.actor_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await _registry.execute(body.tool_name, body.arguments, context)
    return result.model_dump()
