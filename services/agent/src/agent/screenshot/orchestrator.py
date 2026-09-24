"""Screenshot-to-code orchestrator."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from ai_platform_protocol.agent import AgentEventType, AgentRunConfig, AgentRunStatus
from ai_platform_protocol.ui import UIValidationMode
from ai_platform_protocol.vision import (
    ImageInput,
    RenderRequest,
    ScreenshotToCodeRequest,
    ScreenshotToCodeResult,
    VisionErrorCode,
    VisionRequest,
)

from agent.config import ScreenshotSettings, load_screenshot_settings
from agent.loop.events import EventSink, InMemoryEventSink
from agent.loop.runner import LoopAgentRunner
from agent.loop.store import get_run_store
from agent.render.factory import create_renderer
from agent.screenshot.converter import visual_analysis_to_ui_spec
from agent.screenshot.planner import ScreenshotUIPlanner
from agent.screenshot.prompts import build_screenshot_task
from agent.screenshot.store import get_screenshot_run_store
from agent.services.workspace_resolver import build_context
from agent.ui.context import build_ui_context
from agent.ui.detector import detect_framework_profile
from agent.ui.validator import UIValidator
from agent.vision.errors import VisionError
from agent.vision.image import ImageValidator
from agent.vision.providers.base import VisionProvider
from agent.visual.comparator import VisualComparator


class ScreenshotToCodeOrchestrator:
    def __init__(
        self,
        *,
        runner: LoopAgentRunner,
        vision_provider: VisionProvider,
        settings: ScreenshotSettings | None = None,
    ) -> None:
        self._runner = runner
        self._vision = vision_provider
        self._settings = settings or load_screenshot_settings()
        self._store = get_screenshot_run_store()
        self._image_validator = ImageValidator(
            max_bytes=self._settings.max_image_bytes,
            max_width=self._settings.max_width,
            max_height=self._settings.max_height,
            max_pixels=self._settings.max_pixels,
        )
        self._planner = ScreenshotUIPlanner()
        self._comparator = VisualComparator(threshold=self._settings.visual_threshold)
        self._renderer = create_renderer()

    async def generate(
        self,
        request: ScreenshotToCodeRequest,
        *,
        event_sink: EventSink | None = None,
    ) -> ScreenshotToCodeResult:
        if not self._settings.enabled:
            raise VisionError(
                VisionErrorCode.VISION_PROVIDER_UNAVAILABLE,
                "Screenshot-to-code is disabled",
            )
        if not request.images:
            raise VisionError(VisionErrorCode.INVALID_IMAGE, "At least one image is required")

        started = time.perf_counter()
        request_id = request.request_id or str(uuid.uuid4())
        sink = event_sink or InMemoryEventSink()
        run_id = str(uuid.uuid4())

        sink.emit(
            run_id,
            AgentEventType.IMAGE_RECEIVED,
            {"count": len(request.images), "workspace_id": request.workspace_id},
        )

        validated_images: list[ImageInput] = []
        for img in request.images:
            meta = self._image_validator.validate(img)
            validated_images.append(
                ImageInput(
                    data=img.data,
                    mime_type=meta.mime_type,
                    filename=img.filename,
                    image_id=meta.image_id,
                    viewport=img.viewport,
                )
            )

        root_path = self._resolve_root(request)
        profile = detect_framework_profile(root_path)
        if request.framework:
            profile.framework = request.framework
        ui_context = build_ui_context(root_path, profile=profile)

        sink.emit(run_id, AgentEventType.VISION_STARTED, {})
        try:
            vision_response = await self._vision.analyze(
                VisionRequest(
                    images=validated_images,
                    prompt=request.prompt,
                    metadata={"fixture_name": request.prompt},
                )
            )
        except VisionError:
            raise
        except Exception as exc:
            raise VisionError(VisionErrorCode.VISION_ANALYSIS_FAILED, str(exc)) from exc

        analysis = vision_response.analysis
        analysis.source_image_id = validated_images[0].image_id
        sink.emit(
            run_id,
            AgentEventType.VISION_COMPLETED,
            {"confidence": analysis.overall_confidence},
        )

        spec = visual_analysis_to_ui_spec(analysis, prompt=request.prompt, route=request.route)
        spec.framework = request.framework or profile.framework
        spec.styling_system = profile.styling_system
        plan = self._planner.plan(
            analysis=analysis,
            spec=spec,
            context=ui_context,
            route=request.route,
            validation_mode=request.validation_mode.value,
        )
        sink.emit(run_id, AgentEventType.UI_SPEC_CREATED, {"spec": spec.model_dump()})
        sink.emit(run_id, AgentEventType.UI_PLAN_CREATED, {"plan": plan.model_dump()})

        visual_validation = None
        visual_iterations = 0
        max_visual = request.max_visual_iterations or self._settings.max_visual_iterations
        reference_bytes = validated_images[0].data
        agent_result = None
        validation = None
        files_created: list[str] = []
        files_modified: list[str] = []

        while visual_iterations <= max_visual:
            task = build_screenshot_task(
                spec=spec,
                plan=plan,
                context=ui_context,
                analysis=analysis,
                visual_feedback=visual_validation,
            )
            if visual_iterations > 0:
                sink.emit(
                    run_id,
                    AgentEventType.VISUAL_FIX_STARTED,
                    {"iteration": visual_iterations},
                )

            agent_config = AgentRunConfig(
                workspace_id=request.workspace_id,
                workspace_root=str(root_path),
                task=task,
                policy="ui_generation",
                max_iterations=self._settings.max_iterations,
                request_id=request_id,
                actor_id=request.actor_id,
                validation_mode=request.validation_mode.value,
            )
            sink.emit(
                run_id, AgentEventType.UI_GENERATION_STARTED, {"iteration": visual_iterations}
            )
            agent_result = await self._runner.run(
                agent_config,
                event_sink=sink,
                root_path=str(root_path),
            )
            run_id = agent_result.run_id
            files_created, files_modified = _track_file_changes(agent_result.run_id)

            validation = None
            if request.validation_mode != UIValidationMode.NONE:
                sink.emit(
                    run_id,
                    AgentEventType.UI_VALIDATION_STARTED,
                    {"mode": request.validation_mode.value},
                )
                tool_context = build_context(
                    workspace_id=request.workspace_id,
                    root_path=str(root_path),
                    request_id=request_id,
                    actor_id=request.actor_id,
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
                if not validation.success:
                    break

            if not (request.visual_validation_enabled and self._settings.visual_validation_enabled):
                break

            sink.emit(run_id, AgentEventType.RENDER_STARTED, {})
            render_result = await self._renderer.render(
                RenderRequest(
                    workspace_id=request.workspace_id,
                    workspace_root=str(root_path),
                    route=request.route,
                    timeout_sec=self._settings.render_timeout_sec,
                )
            )
            sink.emit(
                run_id,
                AgentEventType.RENDER_COMPLETED,
                {"success": render_result.success},
            )
            if not render_result.success or not render_result.screenshot_bytes:
                break

            sink.emit(run_id, AgentEventType.VISUAL_COMPARISON_STARTED, {})
            threshold = request.visual_validation_threshold or self._settings.visual_threshold
            visual_validation = self._comparator.compare(
                reference_bytes,
                render_result.screenshot_bytes,
                analysis=analysis,
                threshold=threshold,
            )
            sink.emit(
                run_id,
                AgentEventType.VISUAL_COMPARISON_COMPLETED,
                {"passed": visual_validation.passed, "score": visual_validation.score},
            )
            if visual_validation.passed:
                break
            visual_iterations += 1
            if visual_iterations > max_visual:
                break

        duration_ms = int((time.perf_counter() - started) * 1000)
        status = agent_result.status.value if agent_result else AgentRunStatus.FAILED.value
        if visual_validation and not visual_validation.passed and visual_iterations > max_visual:
            status = AgentRunStatus.LIMIT_REACHED.value

        result = ScreenshotToCodeResult(
            run_id=run_id,
            request_id=request_id,
            workspace_id=request.workspace_id,
            status=status,
            framework=profile.framework,
            visual_analysis=analysis,
            specification=spec,
            plan=plan,
            files_created=files_created,
            files_modified=files_modified,
            validation=validation if agent_result else None,
            visual_validation=visual_validation,
            visual_iterations=visual_iterations,
            final_response=agent_result.final_response if agent_result else None,
            stop_reason=agent_result.stop_reason if agent_result else None,
            error=agent_result.error if agent_result else None,
            duration_ms=duration_ms,
        )
        self._store.save(result)
        event_type = (
            AgentEventType.SCREENSHOT_COMPLETED
            if status == AgentRunStatus.COMPLETED.value
            else AgentEventType.SCREENSHOT_FAILED
        )
        sink.emit(run_id, event_type, {"status": status})
        return result

    def _resolve_root(self, request: ScreenshotToCodeRequest) -> Path:
        if request.root_path:
            return Path(request.root_path).resolve()
        ctx = build_context(workspace_id=request.workspace_id, root_path=request.root_path)
        return ctx.workspace_root


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
