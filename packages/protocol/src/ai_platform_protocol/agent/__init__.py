"""Agent loop interfaces and types — Phase 6."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class AgentStepType(StrEnum):
    PLAN = "plan"
    RETRIEVE = "retrieve"
    ACT = "act"
    OBSERVE = "observe"
    VALIDATE = "validate"
    REFLECT = "reflect"
    DONE = "done"
    ERROR = "error"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    PROCESSING_RESULT = "processing_result"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LIMIT_REACHED = "limit_reached"


class ModelDecisionType(StrEnum):
    FINAL = "final"
    TOOL_CALL = "tool_call"


class AgentStep(BaseModel):
    type: AgentStepType
    payload: dict[str, Any] = Field(default_factory=dict)


class ModelDecision(BaseModel):
    type: ModelDecisionType
    message: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentObservation(BaseModel):
    tool_name: str
    success: bool
    output: str | None = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentEventType(StrEnum):
    RUN_STARTED = "run.started"
    MODEL_STARTED = "model.started"
    MODEL_DELTA = "model.delta"
    MODEL_COMPLETED = "model.completed"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    OBSERVATION_CREATED = "observation.created"
    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_CANCELLED = "run.cancelled"
    RUN_LIMIT_REACHED = "run.limit_reached"
    UI_ANALYSIS_STARTED = "ui.analysis.started"
    UI_SPEC_CREATED = "ui.spec.created"
    UI_PLAN_CREATED = "ui.plan.created"
    UI_GENERATION_STARTED = "ui.generation.started"
    UI_VALIDATION_STARTED = "ui.validation.started"
    UI_VALIDATION_COMPLETED = "ui.validation.completed"
    UI_COMPLETED = "ui.completed"


class AgentEvent(BaseModel):
    run_id: str
    sequence: int
    event_type: AgentEventType
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRunConfig(BaseModel):
    workspace_id: str
    workspace_root: str | None = None
    task: str
    policy: str = "coding"
    max_iterations: int = 25
    model_id: str = "default"
    request_id: str | None = None
    actor_id: str | None = None
    validation_mode: str = "none"


class AgentRunResult(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    status: AgentRunStatus
    task: str
    policy: str
    final_response: str | None = None
    iterations: int = 0
    tool_calls: int = 0
    model_calls: int = 0
    duration_ms: int = 0
    stop_reason: str | None = None
    error: str | None = None


class AgentRunSummary(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    status: AgentRunStatus
    task: str
    policy: str
    started_at: str
    completed_at: str | None = None
    iterations: int = 0
    tool_calls: int = 0
    model_calls: int = 0
    final_response: str | None = None
    stop_reason: str | None = None
    error: str | None = None


@runtime_checkable
class AgentRunner(Protocol):
    async def run(self, config: AgentRunConfig) -> AgentRunResult: ...

    async def cancel(self, run_id: str) -> bool: ...
