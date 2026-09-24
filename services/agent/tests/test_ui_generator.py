import shutil
from pathlib import Path

import pytest
from agent.config import ToolSettings, UISettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from agent.ui.generator import UIGenerator
from ai_platform_protocol.agent import AgentRunStatus, ModelDecision, ModelDecisionType
from ai_platform_protocol.ui import UIGenerationRequest, UIGenerationTarget, UIValidationMode
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer

FIXTURES = Path(__file__).parent / "fixtures" / "ui"


@pytest.fixture
def vite_workspace(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    indexer = RepositoryIndexer(
        root, workspace_id="ui-ws", config=IndexerConfig(mysql_persistence=False)
    )
    indexer.index(incremental=False)
    return root


@pytest.mark.asyncio
async def test_ui_generation_workflow(vite_workspace):
    tool_settings = ToolSettings(
        enabled=True,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["python", "npm"],
        terminal_denied_commands=["rm"],
        create_parent_dirs=True,
    )
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="code.search",
                arguments={"query": "Button"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": "src/components/Button.tsx"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.write",
                arguments={
                    "path": "src/Login.tsx",
                    "content": "export function LoginPage(){return <div>Login</div>}",
                },
            ),
            ModelDecision(
                type=ModelDecisionType.FINAL,
                message="Created login page reusing Button.",
            ),
        ]
    )
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
    )
    generator = UIGenerator(runner=runner, settings=UISettings(max_iterations=10))
    result = await generator.generate(
        UIGenerationRequest(
            workspace_id="ui-ws",
            prompt="Create a login page",
            target=UIGenerationTarget.PAGE,
            route="/login",
            root_path=str(vite_workspace),
            validation_mode=UIValidationMode.NONE,
        )
    )
    assert result.status == AgentRunStatus.COMPLETED.value
    assert (vite_workspace / "src/Login.tsx").exists()
    assert "src/Login.tsx" in result.files_created


@pytest.mark.asyncio
async def test_ui_read_only_analysis(vite_workspace):
    tool_settings = ToolSettings(enabled=True, write_enabled=True)
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.FINAL, message="Dashboard uses Button in components."
            )
        ]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(tool_settings), model_client=model)
    generator = UIGenerator(runner=runner)
    result = await generator.generate(
        UIGenerationRequest(
            workspace_id="ui-ws",
            prompt="Analyze the dashboard structure",
            target=UIGenerationTarget.ANALYSIS,
            root_path=str(vite_workspace),
            validation_mode=UIValidationMode.NONE,
        )
    )
    assert result.status == AgentRunStatus.COMPLETED.value
    assert result.files_created == []
