"""Agent execution policies."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_platform_protocol.tools import ToolPermission

from agent.loop.errors import AgentErrorCode, AgentExecutionError


@dataclass(frozen=True)
class AgentPolicy:
    name: str
    allow_write: bool = True
    allow_execute: bool = True
    allow_git_read: bool = True
    allowed_tools: frozenset[str] | None = None
    denied_tools: frozenset[str] = field(default_factory=frozenset)
    validation_mode: str = "none"

    def permissions(self) -> set[ToolPermission]:
        perms = {ToolPermission.READ}
        if self.allow_write:
            perms.add(ToolPermission.WRITE)
        if self.allow_execute:
            perms.add(ToolPermission.EXECUTE)
        if self.allow_git_read:
            perms.add(ToolPermission.GIT_READ)
        return perms

    def is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name in self.denied_tools:
            return False
        if self.allowed_tools is not None and tool_name not in self.allowed_tools:
            return False
        if not self.allow_write and tool_name in {"file.write", "file.edit"}:
            return False
        return not (not self.allow_execute and tool_name in {"terminal.exec", "code.diagnostics"})

    def assert_tool_allowed(self, tool_name: str) -> None:
        if not self.is_tool_allowed(tool_name):
            raise AgentExecutionError(
                AgentErrorCode.POLICY_DENIED,
                f"Tool '{tool_name}' is not allowed by policy '{self.name}'",
            )


READ_ONLY_POLICY = AgentPolicy(
    name="read_only",
    allow_write=False,
    allow_execute=False,
    allow_git_read=True,
    allowed_tools=frozenset(
        {
            "file.read",
            "file.list",
            "code.search",
            "code.symbols",
            "code.context",
            "git.status",
            "git.diff",
        }
    ),
)

CODING_POLICY = AgentPolicy(
    name="coding",
    allow_write=True,
    allow_execute=True,
    allow_git_read=True,
    validation_mode="none",
)

TESTING_POLICY = AgentPolicy(
    name="testing",
    allow_write=True,
    allow_execute=True,
    allow_git_read=True,
    validation_mode="diagnostics",
)

UI_READ_ONLY_POLICY = AgentPolicy(
    name="ui_read_only",
    allow_write=False,
    allow_execute=False,
    allow_git_read=True,
    allowed_tools=READ_ONLY_POLICY.allowed_tools,
)

UI_GENERATION_POLICY = AgentPolicy(
    name="ui_generation",
    allow_write=True,
    allow_execute=True,
    allow_git_read=True,
    validation_mode="build",
)

_POLICIES: dict[str, AgentPolicy] = {
    "read_only": READ_ONLY_POLICY,
    "coding": CODING_POLICY,
    "testing": TESTING_POLICY,
    "ui_read_only": UI_READ_ONLY_POLICY,
    "ui_generation": UI_GENERATION_POLICY,
}


def resolve_policy(name: str) -> AgentPolicy:
    policy = _POLICIES.get(name)
    if policy is None:
        raise AgentExecutionError(AgentErrorCode.POLICY_DENIED, f"Unknown policy: {name}")
    return policy
