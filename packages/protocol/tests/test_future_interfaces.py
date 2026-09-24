"""Tests for future protocol interfaces (Phase 4–6)."""

from ai_platform_protocol.agent import AgentRunConfig, AgentStep, AgentStepType
from ai_platform_protocol.indexer import IndexRequest, RepositoryIndexer
from ai_platform_protocol.tools import ToolDefinition, ToolPermission


def test_agent_step_types():
    assert AgentStepType.PLAN == "plan"
    step = AgentStep(type=AgentStepType.ACT, payload={"tool": "read_file"})
    assert step.type == AgentStepType.ACT


def test_agent_run_config():
    cfg = AgentRunConfig(workspace_root="/tmp/ws", task="fix bug")
    assert cfg.max_iterations == 25


def test_tool_definition():
    tool = ToolDefinition(
        name="read_file",
        description="Read a workspace file",
        parameters_schema={"type": "object"},
        permissions=[ToolPermission.READ],
    )
    assert tool.timeout_sec == 120


def test_index_request():
    req = IndexRequest(workspace_root="/tmp/repo")
    assert req.include_globs == ["**/*"]


def test_repository_indexer_protocol():
    class StubIndexer:
        async def index(self, request: IndexRequest) -> None:
            assert request.workspace_root

        async def search(self, query: str, limit: int = 20):
            return []

    assert isinstance(StubIndexer(), RepositoryIndexer)
