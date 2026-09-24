"""Serializable agent run state."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ai_platform_protocol.agent import (
    AgentObservation,
    AgentRunStatus,
    ModelDecision,
)
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentState(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    user_task: str
    policy: str
    status: AgentRunStatus = AgentRunStatus.QUEUED
    messages: list[AgentMessage] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 25
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    observations: list[AgentObservation] = Field(default_factory=list)
    decisions: list[ModelDecision] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    final_response: str | None = None
    error: str | None = None
    stop_reason: str | None = None
    model_calls: int = 0
    total_tool_calls: int = 0

    def append_message(self, role: str, content: str) -> None:
        self.messages.append(AgentMessage(role=role, content=content))

    def mark_completed(self, status: AgentRunStatus, *, response: str | None = None) -> None:
        self.status = status
        self.completed_at = datetime.now(UTC).isoformat()
        if response is not None:
            self.final_response = response
