"""Screenshot-to-code integration tests."""

import base64
import shutil
from pathlib import Path

import pytest
from agent.config import ScreenshotSettings, ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from agent.screenshot.orchestrator import ScreenshotToCodeOrchestrator
from agent.vision.providers.development_mock import DevelopmentMockVisionProvider
from ai_platform_protocol.agent import AgentRunStatus, ModelDecision, ModelDecisionType
from ai_platform_protocol.ui import UIValidationMode
from ai_platform_protocol.vision import ImageInput, ScreenshotToCodeRequest
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer

FIXTURES = Path(__file__).parent / "fixtures"
UI_FIXTURE = FIXTURES / "ui" / "vite-react"
SCREENSHOT_FIXTURE = FIXTURES / "screenshots" / "simple-card"


@pytest.fixture
def vite_workspace(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(UI_FIXTURE, root)
    indexer = RepositoryIndexer(
        root, workspace_id="ss-ws", config=IndexerConfig(mysql_persistence=False)
    )
    indexer.index(incremental=False)
    return root


@pytest.mark.asyncio
async def test_screenshot_to_code_workflow(vite_workspace):
    image_data = (SCREENSHOT_FIXTURE / "reference.png").read_bytes()
    tool_settings = ToolSettings(
        enabled=True,
        write_enabled=True,
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
                tool_name="file.write",
                arguments={
                    "path": "src/ScreenshotCard.tsx",
                    "content": "export function ScreenshotCard(){return <div>Card</div>}",
                },
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="Created card from screenshot."),
        ]
    )
    runner = LoopAgentRunner(
        registry=ToolRegistry(tool_settings),
        model_client=model,
    )
    orchestrator = ScreenshotToCodeOrchestrator(
        runner=runner,
        vision_provider=DevelopmentMockVisionProvider(),
        settings=ScreenshotSettings(
            visual_validation_enabled=True,
            max_visual_iterations=1,
            visual_threshold=0.5,
        ),
    )
    result = await orchestrator.generate(
        ScreenshotToCodeRequest(
            workspace_id="ss-ws",
            images=[
                ImageInput(
                    data=image_data,
                    mime_type="image/png",
                    filename="simple-card.png",
                )
            ],
            prompt="simple-card",
            root_path=str(vite_workspace),
            validation_mode=UIValidationMode.NONE,
            visual_validation_enabled=True,
        )
    )
    assert result.status == AgentRunStatus.COMPLETED.value
    assert result.visual_analysis is not None
    assert result.specification is not None
    assert result.visual_validation is not None
    assert (vite_workspace / "src/ScreenshotCard.tsx").exists()


@pytest.mark.asyncio
async def test_screenshot_api_base64(vite_workspace):
    from unittest.mock import patch

    from agent.main import create_app
    from fastapi.testclient import TestClient

    image_data = (SCREENSHOT_FIXTURE / "reference.png").read_bytes()
    b64 = base64.b64encode(image_data).decode()
    tool_settings = ToolSettings(enabled=True, write_enabled=True, create_parent_dirs=True)
    model = ScriptedModelClient(
        [ModelDecision(type=ModelDecisionType.FINAL, message="Done from screenshot.")]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(tool_settings), model_client=model)
    orchestrator = ScreenshotToCodeOrchestrator(
        runner=runner,
        vision_provider=DevelopmentMockVisionProvider(),
        settings=ScreenshotSettings(visual_validation_enabled=False),
    )
    client = TestClient(create_app())
    with patch("agent.routes.screenshot._build_orchestrator", return_value=orchestrator):
        resp = client.post(
            "/v1/ui/screenshot-to-code",
            json={
                "workspace_id": "ss-ws",
                "image_base64": b64,
                "image_mime_type": "image/png",
                "prompt": "simple-card",
                "root_path": str(vite_workspace),
                "validation_mode": "none",
                "visual_validation_enabled": False,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["visual_analysis"] is not None
