"""Future agent interfaces — Phase 5/6."""

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


class AgentStep(BaseModel):
    type: AgentStepType
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunConfig(BaseModel):
    workspace_root: str
    task: str
    max_iterations: int = 25
    model_id: str = "default"


@runtime_checkable
class AgentRunner(Protocol):
    async def run(self, config: AgentRunConfig) -> None: ...
    async def cancel(self, session_id: str) -> None: ...
