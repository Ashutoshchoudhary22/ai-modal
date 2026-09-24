"""Bounded agent loop runner."""

from __future__ import annotations

import time
import uuid
from typing import Any

from ai_platform_protocol.agent import (
    AgentEventType,
    AgentRunConfig,
    AgentRunResult,
    AgentRunStatus,
    ModelDecisionType,
)
from ai_platform_protocol.tools import ToolPermission

from agent.config import AgentSettings, load_agent_settings
from agent.context import ToolExecutionContext
from agent.loop.cancellation import CancellationToken
from agent.loop.errors import AgentErrorCode, AgentExecutionError
from agent.loop.events import EventSink, InMemoryEventSink
from agent.loop.executor import ToolExecutor
from agent.loop.limits import AgentLimits, LimitCounters, check_limits
from agent.loop.model_client import AgentModelClient
from agent.loop.observer import observation_from_result, observation_to_message
from agent.loop.policy import AgentPolicy, resolve_policy
from agent.loop.state import AgentState
from agent.loop.store import AgentRunStore, get_run_store
from agent.loop.validator import ToolCallValidator
from agent.registry import ToolRegistry
from agent.services.workspace_resolver import build_context


class LoopAgentRunner:
    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        model_client: AgentModelClient | None = None,
        settings: AgentSettings | None = None,
        store: AgentRunStore | None = None,
        event_sink: EventSink | None = None,
    ) -> None:
        self._settings = settings or load_agent_settings()
        self._registry = registry or ToolRegistry()
        self._model_client = model_client
        self._executor = ToolExecutor(self._registry)
        self._validator = ToolCallValidator(self._registry)
        self._store = store or get_run_store()
        self._tokens: dict[str, CancellationToken] = {}

    async def run(
        self,
        config: AgentRunConfig,
        *,
        event_sink: EventSink | None = None,
        root_path: str | None = None,
    ) -> AgentRunResult:
        if not self._settings.enabled:
            raise AgentExecutionError(AgentErrorCode.AGENT_DISABLED, "Agent loop is disabled")
        if self._model_client is None:
            raise AgentExecutionError(
                AgentErrorCode.MODEL_ERROR, "No model client configured for agent run"
            )

        run_id = str(uuid.uuid4())
        request_id = config.request_id or str(uuid.uuid4())
        policy = resolve_policy(config.policy)
        limits = self._build_limits(config)
        sink = event_sink or InMemoryEventSink()
        token = CancellationToken()
        self._tokens[run_id] = token
        counters = LimitCounters()
        started = time.perf_counter()

        try:
            context = build_context(
                workspace_id=config.workspace_id,
                root_path=root_path or config.workspace_root,
                request_id=request_id,
                actor_id=config.actor_id,
            )
        except Exception as exc:
            raise AgentExecutionError(AgentErrorCode.WORKSPACE_NOT_FOUND, str(exc)) from exc

        context.permissions = policy.permissions()
        state = AgentState(
            run_id=run_id,
            request_id=request_id,
            workspace_id=config.workspace_id,
            user_task=config.task,
            policy=policy.name,
            max_iterations=limits.max_iterations,
            status=AgentRunStatus.QUEUED,
        )
        self._store.save_state(state)
        sink.emit(
            run_id,
            AgentEventType.RUN_STARTED,
            {"workspace_id": config.workspace_id, "policy": policy.name, "task": config.task},
        )

        tools_schema = self._tool_schemas(policy)

        while True:
            if token.is_cancelled() or self._store.is_cancelled(run_id):
                state.mark_completed(AgentRunStatus.CANCELLED)
                state.stop_reason = AgentErrorCode.CANCELLED.value
                sink.emit(run_id, AgentEventType.RUN_CANCELLED, {})
                break

            limit_code = check_limits(counters, limits)
            if limit_code:
                state.mark_completed(AgentRunStatus.LIMIT_REACHED)
                state.stop_reason = limit_code.value
                state.error = f"Limit reached: {limit_code.value}"
                sink.emit(
                    run_id,
                    AgentEventType.RUN_LIMIT_REACHED,
                    {"reason": limit_code.value},
                )
                break

            counters.iterations += 1
            state.status = AgentRunStatus.RUNNING
            state.iteration = counters.iterations
            self._store.save_state(state)
            self._trim_messages(state, limits)

            sink.emit(run_id, AgentEventType.MODEL_STARTED, {"iteration": state.iteration})
            try:
                decision = await self._model_client.decide(state, tools_schema)
            except AgentExecutionError as exc:
                state.mark_completed(AgentRunStatus.FAILED)
                state.error = exc.message
                state.stop_reason = exc.code.value
                sink.emit(
                    run_id,
                    AgentEventType.RUN_FAILED,
                    {"error": exc.message, "code": exc.code.value},
                )
                break

            if token.is_cancelled() or self._store.is_cancelled(run_id):
                state.mark_completed(AgentRunStatus.CANCELLED)
                state.stop_reason = AgentErrorCode.CANCELLED.value
                sink.emit(run_id, AgentEventType.RUN_CANCELLED, {})
                break

            counters.model_calls += 1
            state.model_calls = counters.model_calls
            state.decisions.append(decision)
            sink.emit(
                run_id,
                AgentEventType.MODEL_COMPLETED,
                {"type": decision.type.value, "tool_name": decision.tool_name},
            )

            if decision.type == ModelDecisionType.FINAL:
                state.mark_completed(AgentRunStatus.COMPLETED, response=decision.message)
                sink.emit(
                    run_id,
                    AgentEventType.RUN_COMPLETED,
                    {"final_response": decision.message},
                )
                break

            state.status = AgentRunStatus.WAITING_FOR_TOOL
            validation = self._validator.validate(
                decision,
                policy=policy,
                counters=counters,
                limits=limits,
            )
            if not validation.ok:
                from ai_platform_protocol.tools import ToolResult

                obs = observation_from_result(
                    decision.tool_name or "unknown",
                    ToolResult(
                        success=False,
                        error=validation.message,
                        error_code=validation.error_code.value if validation.error_code else None,
                    ),
                    limits,
                )
                state.observations.append(obs)
                state.append_message("assistant", f"Attempted tool: {decision.tool_name}")
                state.append_message("tool", observation_to_message(obs))
                counters.record_retry(decision.tool_name or "unknown")
                state.status = AgentRunStatus.PROCESSING_RESULT
                sink.emit(
                    run_id,
                    AgentEventType.OBSERVATION_CREATED,
                    {"tool_name": decision.tool_name, "success": False},
                )
                continue

            tool_name = decision.tool_name or ""
            arguments = decision.arguments or {}
            sink.emit(
                run_id,
                AgentEventType.TOOL_STARTED,
                {"tool_name": tool_name, "arguments": arguments},
            )
            result = await self._executor.execute(tool_name, arguments, context)
            counters.record_tool_call(tool_name)
            state.total_tool_calls = counters.tool_calls
            state.tool_calls.append({"tool_name": tool_name, "arguments": arguments})
            state.tool_results.append(result.model_dump())

            obs = observation_from_result(tool_name, result, limits)
            state.observations.append(obs)
            state.append_message("assistant", f"Tool call: {tool_name}")
            state.append_message("tool", observation_to_message(obs))
            state.status = AgentRunStatus.PROCESSING_RESULT
            event_type = (
                AgentEventType.TOOL_COMPLETED if result.success else AgentEventType.TOOL_FAILED
            )
            sink.emit(
                run_id,
                event_type,
                {
                    "tool_name": tool_name,
                    "success": result.success,
                    "error_code": result.error_code,
                },
            )
            sink.emit(
                run_id,
                AgentEventType.OBSERVATION_CREATED,
                {"tool_name": tool_name, "success": result.success},
            )

            validation_mode = config.validation_mode or policy.validation_mode
            if validation_mode in {"diagnostics", "tests"} and tool_name in {
                "file.write",
                "file.edit",
            }:
                await self._run_validation(
                    validation_mode, context, state, sink, limits, run_id=run_id
                )

            if not result.success:
                tool_retries = counters.retries_by_tool.get(tool_name, 0)
                if tool_retries < limits.max_retries_per_tool:
                    counters.record_retry(tool_name)

            self._store.save_state(state)

        duration_ms = int((time.perf_counter() - started) * 1000)
        result = AgentRunResult(
            run_id=run_id,
            request_id=request_id,
            workspace_id=config.workspace_id,
            status=state.status,
            task=config.task,
            policy=policy.name,
            final_response=state.final_response,
            iterations=counters.iterations,
            tool_calls=counters.tool_calls,
            model_calls=counters.model_calls,
            duration_ms=duration_ms,
            stop_reason=state.stop_reason,
            error=state.error,
        )
        self._store.save_state(state)
        self._store.save_result(result)
        self._tokens.pop(run_id, None)
        return result

    async def cancel(self, run_id: str) -> bool:
        token = self._tokens.get(run_id)
        if token:
            token.cancel()
        return self._store.request_cancel(run_id)

    def _build_limits(self, config: AgentRunConfig) -> AgentLimits:
        return AgentLimits(
            max_iterations=min(config.max_iterations, self._settings.max_iterations),
            max_tool_calls=self._settings.max_tool_calls,
            max_same_tool_calls=self._settings.max_same_tool_calls,
            max_model_calls=self._settings.max_model_calls,
            max_runtime_sec=self._settings.max_runtime_sec,
            max_context_chars=self._settings.max_context_chars,
            max_tool_result_chars=self._settings.max_tool_result_chars,
            max_history_messages=self._settings.max_history_messages,
            max_retries=self._settings.max_retries,
            max_retries_per_tool=self._settings.max_retries_per_tool,
        )

    def _tool_schemas(self, policy: AgentPolicy) -> list[dict[str, Any]]:
        tools = []
        for tool in self._registry.list():
            if policy.is_tool_allowed(tool.name):
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters_schema": tool.parameters_schema,
                        "permissions": [p.value for p in tool.permissions],
                    }
                )
        return tools

    def _trim_messages(self, state: AgentState, limits: AgentLimits) -> None:
        if len(state.messages) > limits.max_history_messages:
            state.messages = state.messages[-limits.max_history_messages :]
        total = sum(len(m.content) for m in state.messages)
        if total > limits.max_context_chars:
            while state.messages and total > limits.max_context_chars:
                removed = state.messages.pop(0)
                total -= len(removed.content)

    async def _run_validation(
        self,
        mode: str,
        context: ToolExecutionContext,
        state: AgentState,
        sink: EventSink,
        limits: AgentLimits,
        run_id: str | None = None,
    ) -> None:
        run_id = run_id or state.run_id
        sink.emit(run_id, AgentEventType.VALIDATION_STARTED, {"mode": mode})
        tool_name = "code.diagnostics" if mode == "diagnostics" else "terminal.exec"
        if not context.has_permission(ToolPermission.EXECUTE):
            sink.emit(run_id, AgentEventType.VALIDATION_COMPLETED, {"skipped": True})
            return
        args: dict[str, Any] = {} if tool_name == "code.diagnostics" else {"command": "pytest -q"}
        result = await self._executor.execute(tool_name, args, context)
        obs = observation_from_result(tool_name, result, limits)
        state.observations.append(obs)
        state.append_message("tool", observation_to_message(obs))
        sink.emit(
            run_id,
            AgentEventType.VALIDATION_COMPLETED,
            {"success": result.success, "tool_name": tool_name},
        )
