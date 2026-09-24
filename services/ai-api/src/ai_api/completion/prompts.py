"""Completion prompt builder."""

from __future__ import annotations

from ai_platform_protocol.completion import CompletionRequest
from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest

SYSTEM_PROMPT = """You are a code completion engine.
Complete the code at the cursor position.
Return ONLY the code that should be inserted at the cursor.
Do not explain. Do not use markdown fences.
Do not repeat the existing prefix.
Do not repeat code already present in the suffix."""


def build_completion_messages(request: CompletionRequest) -> list[ChatMessage]:
    parts: list[str] = [f"Language: {request.language}", f"File: {request.file_path}"]
    ctx = request.context
    if ctx.current_function:
        parts.append(f"Current function/block:\n{ctx.current_function}")
    if ctx.imports:
        parts.append("Imports:\n" + "\n".join(ctx.imports[:20]))
    if ctx.symbols:
        parts.append("Relevant symbols:\n" + ", ".join(ctx.symbols[:30]))
    if ctx.nearby_code:
        parts.append(f"Nearby code:\n{ctx.nearby_code}")
    if ctx.repository_context:
        parts.append(f"Repository context:\n{ctx.repository_context[:2000]}")
    parts.append(f"<|prefix|>\n{request.prefix}\n<|suffix|>\n{request.suffix}\n<|cursor|>")
    return [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content="\n\n".join(parts)),
    ]


def to_generate_request(request: CompletionRequest, model: str) -> GenerateRequest:
    return GenerateRequest(
        model=model,
        messages=build_completion_messages(request),
        max_tokens=request.options.max_tokens,
        temperature=request.options.temperature,
        stop=request.options.stop or None,
        metadata={"completion_mode": True, "language": request.language},
    )
