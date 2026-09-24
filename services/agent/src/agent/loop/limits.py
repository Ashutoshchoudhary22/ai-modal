"""Agent run limit enforcement."""

from __future__ import annotations

import time
from dataclasses import dataclass

from agent.loop.errors import AgentErrorCode


@dataclass
class AgentLimits:
    max_iterations: int = 25
    max_tool_calls: int = 50
    max_same_tool_calls: int = 10
    max_model_calls: int = 30
    max_runtime_sec: int = 600
    max_context_chars: int = 32_000
    max_tool_result_chars: int = 8_000
    max_history_messages: int = 50
    max_retries: int = 3
    max_retries_per_tool: int = 2


@dataclass
class LimitCounters:
    iterations: int = 0
    tool_calls: int = 0
    model_calls: int = 0
    retries: int = 0
    tool_calls_by_name: dict[str, int] | None = None
    retries_by_tool: dict[str, int] | None = None
    started_at: float = 0.0

    def __post_init__(self) -> None:
        if self.tool_calls_by_name is None:
            self.tool_calls_by_name = {}
        if self.retries_by_tool is None:
            self.retries_by_tool = {}
        if self.started_at == 0.0:
            self.started_at = time.perf_counter()

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_calls += 1
        self.tool_calls_by_name[tool_name] = self.tool_calls_by_name.get(tool_name, 0) + 1

    def record_retry(self, tool_name: str) -> None:
        self.retries += 1
        self.retries_by_tool[tool_name] = self.retries_by_tool.get(tool_name, 0) + 1

    def elapsed_sec(self) -> float:
        return time.perf_counter() - self.started_at


def check_limits(counters: LimitCounters, limits: AgentLimits) -> AgentErrorCode | None:
    if counters.iterations >= limits.max_iterations:
        return AgentErrorCode.ITERATION_LIMIT
    if counters.tool_calls >= limits.max_tool_calls:
        return AgentErrorCode.TOOL_CALL_LIMIT
    if counters.model_calls >= limits.max_model_calls:
        return AgentErrorCode.MODEL_CALL_LIMIT
    if counters.elapsed_sec() >= limits.max_runtime_sec:
        return AgentErrorCode.RUNTIME_LIMIT
    if counters.retries >= limits.max_retries:
        return AgentErrorCode.ITERATION_LIMIT
    return None


def check_same_tool_limit(
    counters: LimitCounters, tool_name: str, limits: AgentLimits
) -> AgentErrorCode | None:
    count = counters.tool_calls_by_name.get(tool_name, 0)
    if count >= limits.max_same_tool_calls:
        return AgentErrorCode.TOOL_CALL_LIMIT
    return None
