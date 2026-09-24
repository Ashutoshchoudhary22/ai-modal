"""Future tool interfaces — Phase 5."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ToolPermission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    GIT_READ = "git_read"
    NETWORK = "network"
    BROWSER = "browser"


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters_schema: dict[str, Any]
    permissions: list[ToolPermission] = Field(default_factory=list)
    timeout_sec: int = 120


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    workspace_id: str
    request_id: str


class ToolResult(BaseModel):
    success: bool
    output: str | None = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Tool(Protocol):
    definition: ToolDefinition

    async def execute(self, arguments: dict[str, Any]) -> ToolResult: ...
