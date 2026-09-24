"""Protocol package tests."""

import pytest
from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest


def test_generate_request_validation() -> None:
    req = GenerateRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        max_tokens=100,
    )
    assert req.model == "default"
    assert len(req.messages) == 1


def test_generate_request_prompt_only() -> None:
    req = GenerateRequest(prompt="Hello", system_prompt="You are helpful")
    messages = req.resolved_messages()
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"


def test_generate_request_requires_prompt_or_messages() -> None:
    with pytest.raises(ValueError):
        GenerateRequest()


def test_generate_request_temperature_bounds() -> None:
    req = GenerateRequest(
        messages=[ChatMessage(role="user", content="Hi")],
        temperature=0.0,
    )
    assert req.temperature == 0.0
