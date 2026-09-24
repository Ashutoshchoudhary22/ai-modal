import shutil
from pathlib import Path
from unittest.mock import patch

from agent.config import ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.main import create_app
from agent.registry import ToolRegistry
from agent.ui.generator import UIGenerator
from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parent / "fixtures" / "ui"


def test_post_ui_generate(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    settings = ToolSettings(enabled=True, write_enabled=True, create_parent_dirs=True)
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.write",
                arguments={"path": "src/pages/Pricing.tsx", "content": "export const x=1"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="Done"),
        ]
    )
    generator = UIGenerator(
        runner=LoopAgentRunner(registry=ToolRegistry(settings), model_client=model)
    )
    client = TestClient(create_app())
    with patch("agent.routes.ui._build_generator", return_value=generator):
        resp = client.post(
            "/v1/ui/generate",
            json={
                "workspace_id": "ws",
                "prompt": "Create pricing page",
                "root_path": str(root),
                "validation_mode": "none",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_get_ui_run(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    settings = ToolSettings(enabled=True, write_enabled=True, create_parent_dirs=True)
    model = ScriptedModelClient([ModelDecision(type=ModelDecisionType.FINAL, message="Done")])
    generator = UIGenerator(
        runner=LoopAgentRunner(registry=ToolRegistry(settings), model_client=model)
    )
    client = TestClient(create_app())
    with patch("agent.routes.ui._build_generator", return_value=generator):
        create = client.post(
            "/v1/ui/generate",
            json={
                "workspace_id": "ws",
                "prompt": "Analyze UI",
                "target": "analysis",
                "root_path": str(root),
                "validation_mode": "none",
            },
        )
    run_id = create.json()["run_id"]
    get = client.get(f"/v1/ui/runs/{run_id}")
    assert get.status_code == 200
