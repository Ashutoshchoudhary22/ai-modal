"""Agent API tests."""

from unittest.mock import patch

from agent.config import ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.main import create_app
from agent.registry import ToolRegistry
from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from fastapi.testclient import TestClient


def _runner_with_scripted(decisions: list[ModelDecision], workspace) -> LoopAgentRunner:
    settings = ToolSettings(
        enabled=True,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["python", "pytest"],
        terminal_denied_commands=["rm"],
        create_parent_dirs=True,
    )
    return LoopAgentRunner(
        registry=ToolRegistry(settings),
        model_client=ScriptedModelClient(decisions),
    )


def test_post_agent_runs(workspace):
    client = TestClient(create_app())
    runner = _runner_with_scripted(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Done.")],
        workspace,
    )
    with patch("agent.routes.agent._build_runner", return_value=runner):
        resp = client.post(
            "/v1/agent/runs",
            json={
                "workspace_id": "ws",
                "task": "test task",
                "policy": "coding",
                "root_path": str(workspace),
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["final_response"] == "Done."


def test_get_agent_run(workspace):
    client = TestClient(create_app())
    runner = _runner_with_scripted(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Done.")],
        workspace,
    )
    with patch("agent.routes.agent._build_runner", return_value=runner):
        create = client.post(
            "/v1/agent/runs",
            json={
                "workspace_id": "ws",
                "task": "test",
                "root_path": str(workspace),
            },
        )
    run_id = create.json()["run_id"]
    get = client.get(f"/v1/agent/runs/{run_id}")
    assert get.status_code == 200
    assert get.json()["run_id"] == run_id


def test_invalid_policy(workspace):
    client = TestClient(create_app())
    runner = _runner_with_scripted([], workspace)
    with patch("agent.routes.agent._build_runner", return_value=runner):
        resp = client.post(
            "/v1/agent/runs",
            json={
                "workspace_id": "ws",
                "task": "test",
                "policy": "unknown_policy",
                "root_path": str(workspace),
            },
        )
    assert resp.status_code == 400


def test_stream_agent_run(workspace):
    client = TestClient(create_app())
    runner = _runner_with_scripted(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Streamed.")],
        workspace,
    )
    with patch("agent.routes.agent._build_runner", return_value=runner):
        resp = client.post(
            "/v1/agent/runs/stream",
            json={
                "workspace_id": "ws",
                "task": "stream test",
                "root_path": str(workspace),
            },
        )
    assert resp.status_code == 200
    assert "run.started" in resp.text or "run.result" in resp.text
