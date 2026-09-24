"""Tests for telemetry context."""

from ai_platform_shared.telemetry import TelemetryContext, get_current_context


def test_telemetry_context_bind_and_log():
    ctx = TelemetryContext(
        request_id="req-1",
        agent_run_id="run-1",
        model_invocation_id="inv-1",
    )
    ctx.bind()
    current = get_current_context()
    assert current.request_id == "req-1"
    assert ctx.as_log_context()["request_id"] == "req-1"
