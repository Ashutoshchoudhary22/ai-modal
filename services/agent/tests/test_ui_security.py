import shutil
from pathlib import Path

import pytest
from agent.config import ToolSettings, UISettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from agent.ui.generator import UIGenerator
from ai_platform_protocol.agent import AgentRunStatus, ModelDecision, ModelDecisionType
from ai_platform_protocol.ui import UIGenerationRequest, UIValidationMode

FIXTURES = Path(__file__).parent / "fixtures" / "ui"


@pytest.mark.asyncio
async def test_ui_denies_env_access(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    (root / ".env").write_text("SECRET=1", encoding="utf-8")
    tool_settings = ToolSettings(enabled=True, write_enabled=True)
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": ".env"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    generator = UIGenerator(
        runner=LoopAgentRunner(registry=ToolRegistry(tool_settings), model_client=model),
        settings=UISettings(),
    )
    result = await generator.generate(
        UIGenerationRequest(
            workspace_id="ws",
            prompt="Read env for theme",
            root_path=str(root),
            validation_mode=UIValidationMode.NONE,
        )
    )
    assert result.status == AgentRunStatus.COMPLETED.value
    state = generator._runner._store.get_state(result.run_id)
    assert state and any(not o.success for o in state.observations)


@pytest.mark.asyncio
async def test_ui_denies_terminal_injection(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    tool_settings = ToolSettings(
        enabled=True,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["npm"],
        terminal_denied_commands=["rm"],
    )
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="terminal.exec",
                arguments={"command": "rm -rf ."},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    generator = UIGenerator(
        runner=LoopAgentRunner(registry=ToolRegistry(tool_settings), model_client=model),
    )
    result = await generator.generate(
        UIGenerationRequest(
            workspace_id="ws",
            prompt="Install deps",
            root_path=str(root),
            validation_mode=UIValidationMode.NONE,
        )
    )
    state = generator._runner._store.get_state(result.run_id)
    assert state and any(
        o.tool_name == "terminal.exec" and not o.success for o in state.observations
    )
