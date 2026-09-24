"""UI generation orchestrator using Phase 6 Agent Loop."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from ai_platform_protocol.agent import AgentEventType, AgentRunConfig
from ai_platform_protocol.ui import (
    UIGenerationRequest,
    UIGenerationResult,
    UIGenerationTarget,
    UIValidationMode,
)

from agent.config import UISettings, load_ui_settings
from agent.loop.events import EventSink, InMemoryEventSink
from agent.loop.runner import LoopAgentRunner
from agent.loop.store import get_run_store
from agent.services.workspace_resolver import build_context
from agent.ui.context import build_ui_context
from agent.ui.detector import detect_framework_profile
from agent.ui.planner import create_implementation_plan, create_ui_spec
from agent.ui.prompts import build_ui_task
from agent.ui.store import get_ui_run_store
from agent.ui.validator import UIValidator


class UIGenerator:
    def __init__(
        self,
        *,
        runner: LoopAgentRunner,
        settings: UISettings | None = None,
    ) -> None:
        self._runner = runner
        self._settings = settings or load_ui_settings()
        self._ui_store = get_ui_run_store()

    async def generate(
        self,
        request: UIGenerationRequest,
        *,
        event_sink: EventSink | None = None,
    ) -> UIGenerationResult:
        if not self._settings.enabled:
            raise ValueError("UI generation is disabled")

        started = time.perf_counter()
        request_id = request.request_id or str(uuid.uuid4())
        sink = event_sink or InMemoryEventSink()
        root_path = Path(request.root_path) if request.root_path else None

        if root_path is None:
            ctx = build_context(workspace_id=request.workspace_id, root_path=request.root_path)
            root_path = ctx.workspace_root
        else:
            root_path = root_path.resolve()

        profile = detect_framework_profile(root_path)
        if request.framework:
            profile.framework = request.framework
        ui_context = build_ui_context(root_path, settings=self._settings, profile=profile)

        spec = create_ui_spec(request, ui_context)
        plan = create_implementation_plan(spec, ui_context, request)

        is_analysis = request.target == UIGenerationTarget.ANALYSIS
        policy = "ui_read_only" if is_analysis else "ui_generation"
        validation_mode = "none" if is_analysis else request.validation_mode.value

        task = build_ui_task(request, spec, plan, ui_context)

        agent_config = AgentRunConfig(
            workspace_id=request.workspace_id,
            workspace_root=str(root_path),
            task=task,
            policy=policy,
            max_iterations=self._settings.max_iterations,
            request_id=request_id,
            actor_id=request.actor_id,
            validation_mode=validation_mode,
        )

        agent_result = await self._runner.run(
            agent_config,
            event_sink=sink,
            root_path=str(root_path),
        )
        run_id = agent_result.run_id
        sink.emit(
            run_id,
            AgentEventType.UI_ANALYSIS_STARTED,
            {"workspace_id": request.workspace_id},
        )
        sink.emit(run_id, AgentEventType.UI_SPEC_CREATED, {"spec": spec.model_dump()})
        sink.emit(run_id, AgentEventType.UI_PLAN_CREATED, {"plan": plan.model_dump()})
        sink.emit(run_id, AgentEventType.UI_GENERATION_STARTED, {"policy": policy})

        tool_context = build_context(
            workspace_id=request.workspace_id,
            root_path=str(root_path),
            request_id=request_id,
            actor_id=request.actor_id,
        )

        validation = None
        if not is_analysis and request.validation_mode != UIValidationMode.NONE:
            sink.emit(
                run_id,
                AgentEventType.UI_VALIDATION_STARTED,
                {"mode": request.validation_mode.value},
            )
            validator = UIValidator(self._runner._registry)
            validation = await validator.validate(
                mode=request.validation_mode,
                profile=profile,
                context=tool_context,
            )
            sink.emit(
                run_id,
                AgentEventType.UI_VALIDATION_COMPLETED,
                {"success": validation.success},
            )

        files_created, files_modified = _track_file_changes(agent_result.run_id)
        duration_ms = int((time.perf_counter() - started) * 1000)

        result = UIGenerationResult(
            run_id=agent_result.run_id,
            request_id=request_id,
            workspace_id=request.workspace_id,
            status=agent_result.status.value,
            framework=profile.framework,
            specification=spec,
            plan=plan,
            files_created=files_created,
            files_modified=files_modified,
            components_created=[c.name for c in spec.components],
            validation=validation,
            final_response=agent_result.final_response,
            stop_reason=agent_result.stop_reason,
            error=agent_result.error,
            duration_ms=duration_ms,
        )
        self._ui_store.save(result)
        sink.emit(run_id, AgentEventType.UI_COMPLETED, {"status": result.status})
        return result


def _track_file_changes(agent_run_id: str) -> tuple[list[str], list[str]]:
    state = get_run_store().get_state(agent_run_id)
    created: list[str] = []
    modified: list[str] = []
    if state is None:
        return created, modified
    for call in state.tool_calls:
        tool = call.get("tool_name")
        args = call.get("arguments", {})
        path = args.get("path")
        if not path:
            continue
        if tool == "file.write":
            created.append(path)
        elif tool == "file.edit":
            modified.append(path)
    return list(dict.fromkeys(created)), list(dict.fromkeys(modified))
