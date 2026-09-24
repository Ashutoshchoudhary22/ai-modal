"""Lightweight tool execution audit log."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock


@dataclass
class AuditRecord:
    request_id: str
    workspace_id: str
    tool_name: str
    actor_id: str | None
    started_at: str
    completed_at: str | None = None
    success: bool = False
    error_type: str | None = None
    duration_ms: int | None = None


class AuditLog:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self._lock = Lock()

    def start(
        self,
        *,
        request_id: str,
        workspace_id: str,
        tool_name: str,
        actor_id: str | None,
    ) -> AuditRecord:
        record = AuditRecord(
            request_id=request_id,
            workspace_id=workspace_id,
            tool_name=tool_name,
            actor_id=actor_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        with self._lock:
            self._records.append(record)
        return record

    def complete(
        self,
        record: AuditRecord,
        *,
        success: bool,
        error_type: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        record.success = success
        record.error_type = error_type
        record.duration_ms = duration_ms
        record.completed_at = datetime.now(UTC).isoformat()

    def list_records(self) -> list[AuditRecord]:
        with self._lock:
            return list(self._records)


_audit_log = AuditLog()


def get_audit_log() -> AuditLog:
    return _audit_log
