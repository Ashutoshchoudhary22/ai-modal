"""Agent loop unit tests with scripted model."""

import pytest
from agent.config import AgentSettings, ToolSettings
from agent.loop.limits import AgentLimits, LimitCounters, check_limits
from agent.loop.model_client import ScriptedModelClient
from agent.loop.policy import READ_ONLY_POLICY
from agent.loop.runner import LoopAgentRunner
from agent.loop.state import AgentState
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
def agent_settings() -> AgentSettings:
    return AgentSettings(
        enabled=True,
        max_iterations=10,
        max_tool_calls=20,
        max_model_calls=10,
        max_runtime_sec=60,
    )


@pytest.fixture
def tool_settings() -> ToolSettings:
    return ToolSettings(
        enabled=True,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["python", "pytest", "echo"],
        terminal_denied_commands=["rm", "del"],
        diagnostics_commands=["python --version"],
        create_parent_dirs=True,
    )


@pytest.fixture
def indexed_workspace(workspace):
    indexer = RepositoryIndexer(
        workspace,
        workspace_id="agent-ws",
        config=IndexerConfig(mysql_persistence=False),
    )
    indexer.index(incremental=False)
    return workspace


def test_limits_iteration_reached():
    from agent.loop.errors import AgentErrorCode

    counters = LimitCounters(iterations=5)
    limits = AgentLimits(max_iterations=5)
    assert check_limits(counters, limits) == AgentErrorCode.ITERATION_LIMIT


def test_read_only_policy_denies_write():
    assert not READ_ONLY_POLICY.is_tool_allowed("file.write")
    assert READ_ONLY_POLICY.is_tool_allowed("file.read")


@pytest.mark.asyncio
async def test_final_response_immediately(workspace, agent_settings, tool_settings):
    model = ScriptedModelClient([ModelDecision(type=ModelDecisionType.FINAL, message="All done.")])
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
        settings=agent_settings,
    )
    result = await runner.run(
        AgentRunConfig(workspace_id="ws", task="say hi", policy="coding"),
        root_path=str(workspace),
    )
    assert result.status == AgentRunStatus.COMPLETED
    assert result.final_response == "All done."
    assert result.tool_calls == 0


@pytest.mark.asyncio
async def test_one_tool_call(workspace, agent_settings, tool_settings):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": "README.md"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="Read complete."),
        ]
    )
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
        settings=agent_settings,
    )
    result = await runner.run(
        AgentRunConfig(workspace_id="ws", task="read readme", policy="coding"),
        root_path=str(workspace),
    )
    assert result.status == AgentRunStatus.COMPLETED
    assert result.tool_calls == 1


@pytest.mark.asyncio
async def test_read_only_denies_write(workspace, agent_settings, tool_settings):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.write",
                arguments={"path": "out.txt", "content": "x"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
        settings=agent_settings,
    )
    result = await runner.run(
        AgentRunConfig(workspace_id="ws", task="write file", policy="read_only"),
        root_path=str(workspace),
    )
    assert result.status == AgentRunStatus.COMPLETED
    assert result.tool_calls == 0


@pytest.mark.asyncio
async def test_iteration_limit(workspace, agent_settings, tool_settings):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": "README.md"},
            )
        ]
        * 20
    )
    settings = AgentSettings(max_iterations=3, max_tool_calls=100, max_model_calls=100)
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
        settings=settings,
    )
    result = await runner.run(
        AgentRunConfig(workspace_id="ws", task="loop", policy="coding", max_iterations=3),
        root_path=str(workspace),
    )
    assert result.status == AgentRunStatus.LIMIT_REACHED


@pytest.mark.asyncio
async def test_cancellation(workspace, agent_settings, tool_settings):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.read",
                arguments={"path": "README.md"},
            )
        ]
        * 10
        + [ModelDecision(type=ModelDecisionType.FINAL, message="done")]
    )
    settings = AgentSettings(max_iterations=100, max_tool_calls=100, max_model_calls=100)
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
        settings=settings,
    )
    config = AgentRunConfig(workspace_id="ws", task="cancel me", policy="coding")
    original_save = runner._store.save_state
    cancelled = False

    def capture_save(state):
        nonlocal cancelled
        original_save(state)
        if not cancelled:
            cancelled = True
            token = runner._tokens.get(state.run_id)
            if token:
                token.cancel()
            runner._store.request_cancel(state.run_id)

    runner._store.save_state = capture_save  # type: ignore[method-assign]
    result = await runner.run(config, root_path=str(workspace))
    assert result.status == AgentRunStatus.CANCELLED


def test_agent_state_serializable():
    state = AgentState(
        run_id="r1",
        request_id="req",
        workspace_id="ws",
        user_task="task",
        policy="coding",
    )
    data = state.model_dump()
    assert data["run_id"] == "r1"
