"""End-to-end agent workflow with real tools."""

import pytest
from agent.config import AgentSettings, ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from ai_platform_protocol.agent import (
    AgentRunConfig,
    AgentRunStatus,
    ModelDecision,
    ModelDecisionType,
)
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer


@pytest.fixture
def agent_tool_settings() -> ToolSettings:
    return ToolSettings(
        enabled=True,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["python", "pytest", "echo"],
        terminal_denied_commands=["rm", "del"],
        diagnostics_commands=["python --version"],
        create_parent_dirs=True,
    )


@pytest.mark.asyncio
async def test_agent_workflow_search_read_edit(workspace, agent_tool_settings):
    indexer = RepositoryIndexer(
        workspace,
        workspace_id="agent-ws",
        config=IndexerConfig(mysql_persistence=False),
    )
    indexer.index(incremental=False)

    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="code.search",
                arguments={"query": "create_connection"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": "src/app.py"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.edit",
                arguments={
                    "path": "src/app.py",
                    "old_text": "PORT = 3000",
                    "new_text": "PORT = 4000",
                },
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="terminal.exec",
                arguments={"command": "python --version"},
            ),
            ModelDecision(
                type=ModelDecisionType.FINAL,
                message="Updated port and verified Python.",
            ),
        ]
    )
    runner = LoopAgentRunner(
        registry=ToolRegistry(agent_tool_settings),
        model_client=model,
        settings=AgentSettings(max_iterations=10),
    )
    result = await runner.run(
        AgentRunConfig(workspace_id="agent-ws", task="Update port in app.py", policy="coding"),
        root_path=str(workspace),
    )
    assert result.status == AgentRunStatus.COMPLETED
    assert result.tool_calls == 4
    content = (workspace / "src" / "app.py").read_text(encoding="utf-8")
    assert "4000" in content
