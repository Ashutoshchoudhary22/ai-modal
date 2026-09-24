"""UI validation abstraction."""

from __future__ import annotations

import time
from typing import Any

from ai_platform_protocol.tools import ToolResult
from ai_platform_protocol.ui import UIFrameworkProfile, UIValidationMode, UIValidationResult

from agent.context import ToolExecutionContext
from agent.loop.executor import ToolExecutor
from agent.registry import ToolRegistry


class UIValidator:
    def __init__(self, registry: ToolRegistry, executor: ToolExecutor | None = None) -> None:
        self._registry = registry
        self._executor = executor or ToolExecutor(registry)

    async def validate(
        self,
        *,
        mode: UIValidationMode,
        profile: UIFrameworkProfile,
        context: ToolExecutionContext,
    ) -> UIValidationResult:
        started = time.perf_counter()
        errors: list[str] = []
        warnings: list[str] = []
        diagnostics: dict[str, Any] | None = None
        build: dict[str, Any] | None = None
        tests: dict[str, Any] | None = None
        success = True

        if mode == UIValidationMode.NONE:
            return UIValidationResult(success=True, duration_ms=0)

        if mode in {
            UIValidationMode.DIAGNOSTICS,
            UIValidationMode.BUILD,
            UIValidationMode.TEST,
            UIValidationMode.FULL,
        }:
            diagnostics = await self._run_tool("code.diagnostics", {}, context)
            if not diagnostics.get("success"):
                success = False
                errors.append(diagnostics.get("error") or "Diagnostics failed")

        if mode in {UIValidationMode.BUILD, UIValidationMode.FULL}:
            if profile.build_command:
                build = await self._run_terminal(profile.build_command, context)
                if not build.get("success"):
                    success = False
                    errors.append(build.get("stderr") or "Build failed")
            else:
                warnings.append("No build script configured")

        if mode in {UIValidationMode.TEST, UIValidationMode.FULL}:
            if profile.test_command:
                tests = await self._run_terminal(profile.test_command, context)
                if not tests.get("success"):
                    success = False
                    errors.append(tests.get("stderr") or "Tests failed")
            else:
                warnings.append("No test script configured")

        duration = int((time.perf_counter() - started) * 1000)
        return UIValidationResult(
            success=success,
            diagnostics=diagnostics,
            build=build,
            tests=tests,
            errors=errors,
            warnings=warnings,
            duration_ms=duration,
        )

    async def _run_tool(
        self, tool_name: str, args: dict[str, Any], context: ToolExecutionContext
    ) -> dict[str, Any]:
        result: ToolResult = await self._executor.execute(tool_name, args, context)
        return {
            "success": result.success,
            "error": result.error,
            "metadata": result.metadata,
        }

    async def _run_terminal(self, command: str, context: ToolExecutionContext) -> dict[str, Any]:
        result: ToolResult = await self._executor.execute(
            "terminal.exec", {"command": command}, context
        )
        return {
            "success": result.success,
            "stdout": result.metadata.get("stdout", ""),
            "stderr": result.metadata.get("stderr", "") or result.error,
            "exit_code": result.metadata.get("exit_code"),
        }
