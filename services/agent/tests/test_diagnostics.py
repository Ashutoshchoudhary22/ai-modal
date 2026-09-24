import asyncio

from agent.config import ToolSettings
from agent.tools.diagnostics import CodeDiagnosticsTool


def test_diagnostics_runs_configured_command(tool_context):
    settings = ToolSettings(
        terminal_allowed_commands=["python"],
        terminal_denied_commands=["rm", "del"],
        diagnostics_commands=["python --version"],
    )
    result = asyncio.run(CodeDiagnosticsTool(settings).execute({}, tool_context))
    assert result.success
    assert result.metadata["results"]
    entry = result.metadata["results"][0]
    assert entry["command"] == "python --version"
    assert entry["exit_code"] is not None


def test_diagnostics_empty_config(tool_context):
    settings = ToolSettings(diagnostics_commands=[])
    result = asyncio.run(CodeDiagnosticsTool(settings).execute({}, tool_context))
    assert result.success
    assert result.metadata["results"] == []
