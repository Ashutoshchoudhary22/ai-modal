"""Chat context preparation tests."""

from ai_api.services.chat_context import prepare_generate_request
from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest
from ai_platform_shared.config import Settings


def test_injects_system_prompt_when_missing() -> None:
    settings = Settings(chat_system_prompt="You are helpful.")
    prepared = prepare_generate_request(
        GenerateRequest(messages=[ChatMessage(role="user", content="hiee")]),
        settings,
    )
    assert prepared.messages[0].role == "system"
    assert prepared.messages[0].content == "You are helpful."
    assert prepared.messages[-1].content == "hiee"


def test_preserves_existing_system_prompt() -> None:
    settings = Settings(chat_system_prompt="Default system")
    prepared = prepare_generate_request(
        GenerateRequest(
            messages=[
                ChatMessage(role="system", content="Custom system"),
                ChatMessage(role="user", content="hello"),
            ]
        ),
        settings,
    )
    assert prepared.messages[0].content == "Custom system"
    assert sum(1 for m in prepared.messages if m.role == "system") == 1


def test_trims_history_and_keeps_recent_turns() -> None:
    settings = Settings(chat_system_prompt="", chat_max_history_messages=3)
    prepared = prepare_generate_request(
        GenerateRequest(
            messages=[
                ChatMessage(role="user", content="1"),
                ChatMessage(role="assistant", content="2"),
                ChatMessage(role="user", content="3"),
                ChatMessage(role="assistant", content="4"),
            ]
        ),
        settings,
    )
    assert len(prepared.messages) == 3
    assert prepared.messages[-1].content == "4"


def test_includes_rag_context() -> None:
    settings = Settings(chat_system_prompt="")
    prepared = prepare_generate_request(
        GenerateRequest(messages=[ChatMessage(role="user", content="What is UserService?")]),
        settings,
        rag_context="symbol class UserService (UserService.ts)",
    )
    assert any("UserService" in message.content for message in prepared.messages)
