"""In-memory agent run store."""

from __future__ import annotations

import threading

from ai_platform_protocol.agent import AgentRunResult, AgentRunSummary

from agent.loop.state import AgentState


class AgentRunStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._states: dict[str, AgentState] = {}
        self._results: dict[str, AgentRunResult] = {}
        self._cancellation_flags: dict[str, bool] = {}

    def save_state(self, state: AgentState) -> None:
        with self._lock:
            self._states[state.run_id] = state

    def get_state(self, run_id: str) -> AgentState | None:
        with self._lock:
            return self._states.get(run_id)

    def save_result(self, result: AgentRunResult) -> None:
        with self._lock:
            self._results[result.run_id] = result

    def get_result(self, run_id: str) -> AgentRunResult | None:
        with self._lock:
            return self._results.get(run_id)

    def request_cancel(self, run_id: str) -> bool:
        with self._lock:
            if run_id not in self._states and run_id not in self._results:
                return False
            self._cancellation_flags[run_id] = True
            return True

    def is_cancelled(self, run_id: str) -> bool:
        with self._lock:
            return self._cancellation_flags.get(run_id, False)

    def summary(self, run_id: str) -> AgentRunSummary | None:
        state = self.get_state(run_id)
        result = self.get_result(run_id)
        if state is None and result is None:
            return None
        if result is not None:
            return AgentRunSummary(
                run_id=result.run_id,
                request_id=result.request_id,
                workspace_id=result.workspace_id,
                status=result.status,
                task=result.task,
                policy=result.policy,
                started_at=state.started_at if state else "",
                completed_at=state.completed_at if state else None,
                iterations=result.iterations,
                tool_calls=result.tool_calls,
                model_calls=result.model_calls,
                final_response=result.final_response,
                stop_reason=result.stop_reason,
                error=result.error,
            )
        assert state is not None
        return AgentRunSummary(
            run_id=state.run_id,
            request_id=state.request_id,
            workspace_id=state.workspace_id,
            status=state.status,
            task=state.user_task,
            policy=state.policy,
            started_at=state.started_at,
            completed_at=state.completed_at,
            iterations=state.iteration,
            tool_calls=state.total_tool_calls,
            model_calls=state.model_calls,
            final_response=state.final_response,
            stop_reason=state.stop_reason,
            error=state.error,
        )


_STORE = AgentRunStore()


def get_run_store() -> AgentRunStore:
    return _STORE
