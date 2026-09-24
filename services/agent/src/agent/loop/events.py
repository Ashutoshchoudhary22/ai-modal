"""Agent event sink abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from ai_platform_protocol.agent import AgentEvent, AgentEventType


class EventSink(ABC):
    @abstractmethod
    def emit(self, run_id: str, event_type: AgentEventType, metadata: dict[str, Any]) -> AgentEvent:
        raise NotImplementedError

    @abstractmethod
    def list_events(self, run_id: str) -> list[AgentEvent]:
        raise NotImplementedError


class InMemoryEventSink(EventSink):
    def __init__(self) -> None:
        self._sequence: dict[str, int] = {}
        self._events: dict[str, list[AgentEvent]] = {}

    def emit(self, run_id: str, event_type: AgentEventType, metadata: dict[str, Any]) -> AgentEvent:
        seq = self._sequence.get(run_id, 0) + 1
        self._sequence[run_id] = seq
        event = AgentEvent(
            run_id=run_id,
            sequence=seq,
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            metadata=metadata,
        )
        self._events.setdefault(run_id, []).append(event)
        return event

    def list_events(self, run_id: str) -> list[AgentEvent]:
        return list(self._events.get(run_id, []))
