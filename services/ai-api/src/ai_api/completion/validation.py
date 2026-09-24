"""Completion response validation and sanitization."""

from __future__ import annotations

import re

MAX_COMPLETION_CHARS = 16_384
MAX_COMPLETION_LINES = 20
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_completion(
    text: str, prefix: str, suffix: str, max_lines: int = MAX_COMPLETION_LINES
) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = CONTROL_CHARS.sub("", cleaned)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[\w]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    if prefix and cleaned.startswith(prefix):
        cleaned = cleaned[len(prefix) :]
    if suffix and cleaned.endswith(suffix):
        cleaned = cleaned[: -len(suffix)]
    lines = cleaned.split("\n")
    if len(lines) > max_lines:
        cleaned = "\n".join(lines[:max_lines])
    if len(cleaned) > MAX_COMPLETION_CHARS:
        cleaned = cleaned[:MAX_COMPLETION_CHARS]
    return cleaned


def check_balanced_delimiters(text: str) -> bool:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    for ch in text:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in pairs.values() and (not stack or stack.pop() != ch):
            return False
    return len(stack) == 0
