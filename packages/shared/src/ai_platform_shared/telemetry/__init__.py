"""Lightweight observability context — extensible for OpenTelemetry later."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_agent_run_id: ContextVar[str | None] = ContextVar("agent_run_id", default=None)
_model_invocation_id: ContextVar[str | None] = ContextVar("model_invocation_id", default=None)


@dataclass
class TelemetryContext:
    request_id: str | None = None
    agent_run_id: str | None = None
    model_invocation_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def bind(self) -> None:
        if self.request_id is not None:
            _request_id.set(self.request_id)
        if self.agent_run_id is not None:
            _agent_run_id.set(self.agent_run_id)
        if self.model_invocation_id is not None:
            _model_invocation_id.set(self.model_invocation_id)

    def as_log_context(self) -> dict[str, Any]:
        ctx: dict[str, Any] = {}
        if self.request_id:
            ctx["request_id"] = self.request_id
        if self.agent_run_id:
            ctx["agent_run_id"] = self.agent_run_id
        if self.model_invocation_id:
            ctx["model_invocation_id"] = self.model_invocation_id
        ctx.update(self.extra)
        return ctx


def get_current_context() -> TelemetryContext:
    return TelemetryContext(
        request_id=_request_id.get(),
        agent_run_id=_agent_run_id.get(),
        model_invocation_id=_model_invocation_id.get(),
    )
