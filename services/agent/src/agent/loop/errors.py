"""Agent loop error codes."""

from __future__ import annotations

from enum import StrEnum


class AgentErrorCode(StrEnum):
    TOOL_NOT_FOUND = "tool_not_found"
    INVALID_ARGUMENTS = "invalid_arguments"
    PERMISSION_DENIED = "permission_denied"
    SECURITY_DENIED = "security_denied"
    TOOL_FAILED = "tool_failed"
    COMMAND_TIMEOUT = "command_timeout"
    MODEL_ERROR = "model_error"
    MODEL_INVALID_RESPONSE = "model_invalid_response"
    CONTEXT_LIMIT = "context_limit"
    ITERATION_LIMIT = "iteration_limit"
    TOOL_CALL_LIMIT = "tool_call_limit"
    RUNTIME_LIMIT = "runtime_limit"
    MODEL_CALL_LIMIT = "model_call_limit"
    CANCELLED = "cancelled"
    POLICY_DENIED = "policy_denied"
    WORKSPACE_NOT_FOUND = "workspace_not_found"
    AGENT_DISABLED = "agent_disabled"


class AgentExecutionError(Exception):
    def __init__(self, code: AgentErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
