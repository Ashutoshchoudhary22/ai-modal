"""Browser agent integration tests."""

import pytest
from agent.browser.orchestrator import BrowserAgentOrchestrator
from agent.config import ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from ai_platform_protocol.browser import BrowserRunRequest


@pytest.mark.asyncio
async def test_complete_browser_flow(tmp_path):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="browser.click",
                arguments={"element_id": "e2"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="Reached dashboard"),
        ]
    )
    settings = ToolSettings(enabled=True)
    runner = LoopAgentRunner(registry=ToolRegistry(settings), model_client=model)
    orchestrator = BrowserAgentOrchestrator(runner=runner)
    result = await orchestrator.run(
        BrowserRunRequest(
            workspace_id="browser-ws",
            task="Click continue and verify dashboard",
            start_url="https://example.com/simple",
            allowed_domains=["example.com"],
        ),
        root_path=str(tmp_path),
    )
    assert result.status == "completed"
    assert result.final_response == "Reached dashboard"
    assert result.current_url == "https://example.com/dashboard"
    assert result.navigation_count >= 1


@pytest.mark.asyncio
async def test_browser_form_fill_flow(tmp_path):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="browser.fill",
                arguments={"element_id": "e1", "value": "user@example.com"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="browser.fill",
                arguments={"element_id": "e2", "value": "password"},
            ),
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="browser.click",
                arguments={"element_id": "e4"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="Logged in"),
        ]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(ToolSettings(enabled=True)), model_client=model)
    orchestrator = BrowserAgentOrchestrator(runner=runner)
    result = await orchestrator.run(
        BrowserRunRequest(
            workspace_id="browser-ws",
            task="Fill login form and submit",
            start_url="https://example.com/login",
            allowed_domains=["example.com"],
        ),
        root_path=str(tmp_path),
    )
    assert result.status == "completed"
    assert result.current_url == "https://example.com/dashboard"
