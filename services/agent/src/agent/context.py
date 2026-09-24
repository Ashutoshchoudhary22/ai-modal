"""Tool execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ai_platform_protocol.tools import ToolPermission


@dataclass
class ToolExecutionContext:
    workspace_id: str
    workspace_root: Path
    request_id: str
    actor_id: str | None = None
    permissions: set[ToolPermission] = field(default_factory=set)
    timeout_sec: int = 120

    def has_permission(self, permission: ToolPermission) -> bool:
        return permission in self.permissions
