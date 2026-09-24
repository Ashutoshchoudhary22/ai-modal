"""Development evaluation model adapter (explicit development_mock designation)."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from training.evaluation.adapters.base import (
    EvaluationModelAdapter,
    GenerationResult,
    ModelCapabilities,
)
from training.evaluation.types import GenerationConfig


class DevelopmentEvaluationAdapter(EvaluationModelAdapter):
    """Deterministic development adapter for benchmark framework validation."""

    def __init__(self, model_id: str = "development-mock-v1") -> None:
        self._model_id = model_id

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            provider_id="development_mock",
            model_id=self._model_id,
            modalities=["text", "image", "multimodal"],
            supports_structured=True,
            supports_multimodal=True,
            supports_agent=True,
            supports_browser=True,
            supports_render=True,
        )

    def _scripted_output(self, sample: dict[str, Any]) -> str | dict[str, Any] | None:
        metadata = sample.get("metadata") or {}
        if "scripted_output" in metadata:
            return metadata["scripted_output"]
        if "scripted_output" in sample:
            return sample["scripted_output"]
        return None

    def generate(
        self, prompt: str, *, config: GenerationConfig, sample: dict[str, Any]
    ) -> GenerationResult:
        started = time.perf_counter()
        scripted = self._scripted_output(sample)
        if isinstance(scripted, dict):
            text = json.dumps(scripted)
            structured = scripted
        elif isinstance(scripted, str):
            text = scripted
            structured = None
        else:
            text = sample.get("reference", "")
            structured = None
        latency = (time.perf_counter() - started) * 1000
        return GenerationResult(
            text=text,
            structured=structured,
            latency_ms=latency,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
        )

    def generate_structured(
        self,
        prompt: str,
        *,
        config: GenerationConfig,
        sample: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> GenerationResult:
        started = time.perf_counter()
        scripted = self._scripted_output(sample)
        if isinstance(scripted, dict):
            structured = scripted
        elif isinstance(scripted, str):
            structured = json.loads(scripted)
        else:
            reference = sample.get("reference")
            structured = reference if isinstance(reference, dict) else {}
        text = json.dumps(structured)
        latency = (time.perf_counter() - started) * 1000
        return GenerationResult(
            text=text,
            structured=structured,
            latency_ms=latency,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
        )

    def multimodal_generate(
        self,
        sample: dict[str, Any],
        *,
        config: GenerationConfig,
        dataset_root: Path,
    ) -> GenerationResult:
        prompt = sample.get("prompt", "")
        if sample.get("messages"):
            prompt = json.dumps(sample["messages"])
        return self.generate_structured(prompt, config=config, sample=sample)

    def agent_execute(
        self, sample: dict[str, Any], *, config: GenerationConfig, workspace: Path
    ) -> GenerationResult:
        from agent.config import ToolSettings
        from agent.loop.model_client import ScriptedModelClient
        from agent.loop.runner import LoopAgentRunner
        from agent.registry import ToolRegistry
        from ai_platform_protocol.agent import AgentRunConfig, ModelDecision, ModelDecisionType

        started = time.perf_counter()
        metadata = sample.get("metadata") or {}
        decisions_raw = metadata.get("scripted_decisions", [])
        decisions = [
            ModelDecision(
                type=ModelDecisionType.FINAL,
                message=metadata.get("expected_final_message", "Task completed."),
            )
        ]
        if decisions_raw:
            decisions = []
            for item in decisions_raw:
                dtype = (
                    ModelDecisionType.FINAL
                    if item.get("type") == "final"
                    else ModelDecisionType.TOOL_CALL
                )
                decisions.append(
                    ModelDecision(
                        type=dtype,
                        message=item.get("message"),
                        tool_name=item.get("tool_name"),
                        arguments=item.get("arguments") or {},
                    )
                )

        runner = LoopAgentRunner(
            registry=ToolRegistry(ToolSettings(enabled=True)),
            model_client=ScriptedModelClient(decisions),
        )

        async def _run() -> Any:
            return await runner.run(
                AgentRunConfig(
                    workspace_id="eval",
                    task=sample.get("task", sample.get("prompt", "")),
                    workspace_root=str(workspace),
                    policy=metadata.get("policy", "coding"),
                ),
                root_path=str(workspace),
            )

        result = asyncio.run(_run())
        latency = (time.perf_counter() - started) * 1000
        expected = metadata.get("expected_final_message", "")
        success = expected in (result.final_response or "")
        return GenerationResult(
            text=result.final_response or "",
            structured={"task_success": success, "status": result.status},
            latency_ms=latency,
        )

    def browser_execute(
        self, sample: dict[str, Any], *, config: GenerationConfig, workspace: Path
    ) -> GenerationResult:
        from agent.browser.orchestrator import BrowserAgentOrchestrator
        from agent.config import ToolSettings
        from agent.loop.model_client import ScriptedModelClient
        from agent.loop.runner import LoopAgentRunner
        from agent.registry import ToolRegistry
        from ai_platform_protocol.agent import ModelDecision, ModelDecisionType

        started = time.perf_counter()
        metadata = sample.get("metadata") or {}
        decisions = [
            ModelDecision(
                type=ModelDecisionType.FINAL,
                message=metadata.get("expected_final_message", "Browser task completed."),
            )
        ]
        runner = LoopAgentRunner(
            registry=ToolRegistry(ToolSettings(enabled=True)),
            model_client=ScriptedModelClient(decisions),
        )
        orchestrator = BrowserAgentOrchestrator(runner=runner)

        from ai_platform_protocol.browser import BrowserRunRequest

        async def _run() -> Any:
            return await orchestrator.run(
                BrowserRunRequest(
                    workspace_id="eval",
                    task=sample.get("task", ""),
                    start_url=metadata.get("start_url", "https://example.com/simple"),
                    allowed_domains=metadata.get("allowed_domains", ["example.com"]),
                ),
                root_path=str(workspace),
            )

        result = asyncio.run(_run())
        latency = (time.perf_counter() - started) * 1000
        expected = metadata.get("expected_status", "completed")
        success = result.status == expected
        return GenerationResult(
            text=result.final_response or "",
            structured={"task_success": success, "status": result.status},
            latency_ms=latency,
        )
