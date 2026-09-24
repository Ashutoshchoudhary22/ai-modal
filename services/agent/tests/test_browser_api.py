"""Browser agent API tests."""

from unittest.mock import patch

from agent.browser.orchestrator import BrowserAgentOrchestrator
from agent.config import ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.main import create_app
from agent.registry import ToolRegistry
from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from fastapi.testclient import TestClient


def _orchestrator_with_model(decisions):
    model = ScriptedModelClient(decisions)
    runner = LoopAgentRunner(registry=ToolRegistry(ToolSettings(enabled=True)), model_client=model)
    return BrowserAgentOrchestrator(runner=runner)


def test_post_browser_run(tmp_path):
    orchestrator = _orchestrator_with_model(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Done")]
    )
    client = TestClient(create_app())
    with patch("agent.routes.browser._build_orchestrator", return_value=orchestrator):
        resp = client.post(
            "/v1/browser/runs",
            json={
                "workspace_id": "ws",
                "task": "Observe page",
                "start_url": "https://example.com/simple",
                "allowed_domains": ["example.com"],
                "root_path": str(tmp_path),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_get_browser_run(tmp_path):
    orchestrator = _orchestrator_with_model(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Done")]
    )
    client = TestClient(create_app())
    with patch("agent.routes.browser._build_orchestrator", return_value=orchestrator):
        create = client.post(
            "/v1/browser/runs",
            json={
                "workspace_id": "ws",
                "task": "Test",
                "start_url": "https://example.com/simple",
                "allowed_domains": ["example.com"],
                "root_path": str(tmp_path),
            },
        )
    run_id = create.json()["run_id"]
    get = client.get(f"/v1/browser/runs/{run_id}")
    assert get.status_code == 200
    assert get.json()["run_id"] == run_id


def test_browser_run_not_found():
    client = TestClient(create_app())
    resp = client.get("/v1/browser/runs/does-not-exist")
    assert resp.status_code == 404


def test_browser_stream_endpoint(tmp_path):
    orchestrator = _orchestrator_with_model(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Streamed")]
    )
    client = TestClient(create_app())
    with patch("agent.routes.browser._build_orchestrator", return_value=orchestrator):
        resp = client.post(
            "/v1/browser/runs/stream",
            json={
                "workspace_id": "ws",
                "task": "Stream test",
                "start_url": "https://example.com/simple",
                "allowed_domains": ["example.com"],
                "root_path": str(tmp_path),
            },
        )
    assert resp.status_code == 200
    assert "browser.result" in resp.text
