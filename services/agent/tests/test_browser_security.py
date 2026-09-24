"""Browser agent security tests."""

import pytest
from agent.browser.orchestrator import BrowserAgentOrchestrator
from agent.config import ToolSettings
from agent.loop.model_client import ScriptedModelClient
from agent.loop.policy import BROWSER_AGENT_POLICY, resolve_policy
from agent.loop.runner import LoopAgentRunner
from agent.registry import ToolRegistry
from ai_platform_protocol.agent import ModelDecision, ModelDecisionType
from ai_platform_protocol.browser import BrowserRunRequest


def test_browser_policy_denies_terminal():
    policy = resolve_policy("browser_agent")
    assert not policy.is_tool_allowed("terminal.exec")
    assert not policy.is_tool_allowed("file.write")
    assert not policy.is_tool_allowed("git.diff")
    assert policy.is_tool_allowed("browser.navigate")
    assert policy.is_tool_allowed("browser.click")


def test_browser_policy_permissions():
    perms = BROWSER_AGENT_POLICY.permissions()
    assert "browser" in {p.value for p in perms}
    assert "execute" not in {p.value for p in perms}
    assert "write" not in {p.value for p in perms}


@pytest.mark.asyncio
async def test_prompt_injection_cannot_run_terminal(tmp_path):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="terminal.exec",
                arguments={"command": "whoami"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(ToolSettings(enabled=True)), model_client=model)
    orchestrator = BrowserAgentOrchestrator(runner=runner)
    result = await orchestrator.run(
        BrowserRunRequest(
            workspace_id="sec-ws",
            task="Follow page instructions",
            start_url="https://example.com/prompt-injection",
            allowed_domains=["example.com"],
        ),
        root_path=str(tmp_path),
    )
    state = runner._store.get_state(result.run_id)
    assert state is not None
    assert any(not o.success for o in state.observations)


@pytest.mark.asyncio
async def test_prompt_injection_cannot_write_file(tmp_path):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="file.write",
                arguments={"path": "evil.txt", "content": "pwned"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(ToolSettings(enabled=True)), model_client=model)
    orchestrator = BrowserAgentOrchestrator(runner=runner)
    result = await orchestrator.run(
        BrowserRunRequest(
            workspace_id="sec-ws",
            task="Ignore page and write file",
            start_url="https://example.com/prompt-injection",
            allowed_domains=["example.com"],
        ),
        root_path=str(tmp_path),
    )
    state = runner._store.get_state(result.run_id)
    assert state and any(not o.success for o in state.observations)
    assert not (tmp_path / "evil.txt").exists()


@pytest.mark.asyncio
async def test_domain_restriction_blocks_navigation(tmp_path):
    model = ScriptedModelClient(
        [
            ModelDecision(
                type=ModelDecisionType.TOOL_CALL,
                tool_name="browser.navigate",
                arguments={"url": "https://evil.example/steal"},
            ),
            ModelDecision(type=ModelDecisionType.FINAL, message="done"),
        ]
    )
    runner = LoopAgentRunner(registry=ToolRegistry(ToolSettings(enabled=True)), model_client=model)
    orchestrator = BrowserAgentOrchestrator(runner=runner)
    result = await orchestrator.run(
        BrowserRunRequest(
            workspace_id="sec-ws",
            task="Visit evil site",
            start_url="https://example.com/simple",
            allowed_domains=["example.com"],
        ),
        root_path=str(tmp_path),
    )
    state = runner._store.get_state(result.run_id)
    assert state and any(
        o.error_code == "domain_not_allowed" for o in state.observations if not o.success
    )
