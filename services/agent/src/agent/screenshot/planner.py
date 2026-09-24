"""Screenshot-to-UI planning using Phase 7 planner."""

from __future__ import annotations

from ai_platform_protocol.ui import (
    ImplementationPlan,
    UIGenerationRequest,
    UIGenerationTarget,
    UIRepositoryContext,
    UISpec,
)
from ai_platform_protocol.vision import VisualAnalysis

from agent.ui.planner import create_implementation_plan


class ScreenshotUIPlanner:
    def plan(
        self,
        *,
        analysis: VisualAnalysis,
        spec: UISpec,
        context: UIRepositoryContext,
        route: str | None = None,
        validation_mode: str = "build",
    ) -> ImplementationPlan:
        request = UIGenerationRequest(
            workspace_id="screenshot",
            prompt=spec.description,
            target=UIGenerationTarget.PAGE,
            route=route,
            validation_mode=validation_mode,
        )
        return create_implementation_plan(spec, context, request)
