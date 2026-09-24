from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.config import ToolSettings
from agent.context import ToolExecutionContext
from agent.registry import ToolRegistry, default_permissions
from agent.ui.validator import UIValidator
from ai_platform_protocol.tools import ToolResult
from ai_platform_protocol.ui import UIFramework, UIFrameworkProfile, UIValidationMode


@pytest.fixture
def tool_context(tmp_path):
    return ToolExecutionContext(
        workspace_id="ws",
        workspace_root=tmp_path,
        request_id="req",
        actor_id="tester",
        permissions=default_permissions(ToolSettings()),
    )


def _profile(**kwargs) -> UIFrameworkProfile:
    return UIFrameworkProfile(framework=UIFramework.VITE_REACT, **kwargs)


@pytest.mark.asyncio
async def test_validation_none(tool_context):
    validator = UIValidator(ToolRegistry(ToolSettings()))
    result = await validator.validate(
        mode=UIValidationMode.NONE, profile=_profile(), context=tool_context
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_validation_diagnostics_success(tool_context):
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=ToolResult(success=True, output="", metadata={"issues": []})
    )
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.DIAGNOSTICS, profile=_profile(), context=tool_context
    )
    assert result.success is True
    assert result.diagnostics is not None


@pytest.mark.asyncio
async def test_validation_diagnostics_failure(tool_context):
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=ToolResult(success=False, error="type errors", metadata={})
    )
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.DIAGNOSTICS, profile=_profile(), context=tool_context
    )
    assert result.success is False
    assert result.errors


@pytest.mark.asyncio
async def test_validation_build_success(tool_context):
    executor = MagicMock()

    async def _execute(tool_name, args, context):
        if tool_name == "code.diagnostics":
            return ToolResult(success=True, output="", metadata={})
        return ToolResult(
            success=True,
            output="ok",
            metadata={"stdout": "built", "stderr": "", "exit_code": 0},
        )

    executor.execute = AsyncMock(side_effect=_execute)
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.BUILD,
        profile=_profile(build_command="npm run build"),
        context=tool_context,
    )
    assert result.success is True
    assert result.build is not None


@pytest.mark.asyncio
async def test_validation_build_failure(tool_context):
    executor = MagicMock()

    async def _execute(tool_name, args, context):
        if tool_name == "code.diagnostics":
            return ToolResult(success=True, output="", metadata={})
        return ToolResult(
            success=False,
            error="build failed",
            metadata={"stdout": "", "stderr": "error TS", "exit_code": 1},
        )

    executor.execute = AsyncMock(side_effect=_execute)
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.BUILD,
        profile=_profile(build_command="npm run build"),
        context=tool_context,
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_validation_missing_build_script_warns(tool_context):
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=ToolResult(success=True, output="", metadata={}))
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.BUILD, profile=_profile(), context=tool_context
    )
    assert "No build script configured" in result.warnings


@pytest.mark.asyncio
async def test_validation_test_mode(tool_context):
    executor = MagicMock()

    async def _execute(tool_name, args, context):
        if tool_name == "code.diagnostics":
            return ToolResult(success=True, output="", metadata={})
        return ToolResult(
            success=True,
            output="",
            metadata={"stdout": "1 passed", "stderr": "", "exit_code": 0},
        )

    executor.execute = AsyncMock(side_effect=_execute)
    validator = UIValidator(ToolRegistry(ToolSettings()), executor=executor)
    result = await validator.validate(
        mode=UIValidationMode.TEST,
        profile=_profile(test_command="npm test"),
        context=tool_context,
    )
    assert result.success is True
    assert result.tests is not None
