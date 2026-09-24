"""Chat request preparation: system prompt, history bounds, RAG context."""

from __future__ import annotations

from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest
from ai_platform_shared.config import Settings


def _trim_history(messages: list[ChatMessage], max_messages: int) -> list[ChatMessage]:
    if len(messages) <= max_messages:
        return messages
    system_messages = [m for m in messages if m.role == "system"]
    non_system = [m for m in messages if m.role != "system"]
    keep = max(1, max_messages - len(system_messages))
    trimmed = non_system[-keep:]
    return system_messages + trimmed


def prepare_generate_request(
    request: GenerateRequest,
    settings: Settings,
    *,
    rag_context: str | None = None,
) -> GenerateRequest:
    messages = list(request.resolved_messages())
    messages = _trim_history(messages, settings.chat_max_history_messages)

    has_system = any(message.role == "system" for message in messages)
    if settings.chat_system_prompt.strip() and not has_system:
        messages.insert(0, ChatMessage(role="system", content=settings.chat_system_prompt.strip()))

    if rag_context and rag_context.strip():
        rag_message = ChatMessage(
            role="system",
            content=(
                "Relevant knowledge (use when helpful; cite sources when available):\n"
                f"{rag_context.strip()}"
            ),
        )
        insert_at = 1 if messages and messages[0].role == "system" else 0
        messages.insert(insert_at, rag_message)

    max_tokens = min(request.max_tokens, settings.model_generation_max_tokens)
    model = request.model
    if model == "default" and settings.model_provider == "local":
        model = settings.default_model or settings.resolved_model_ref

    return request.model_copy(
        update={
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "model": model,
        }
    )


def extract_last_user_message(messages: list[ChatMessage]) -> str | None:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()
    return None
