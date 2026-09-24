"""Deterministic development mock completions."""

from __future__ import annotations

import re

MOCK_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bfunction\s*$", re.M), "example() {\n    return null;\n}"),
    (re.compile(r"\bconst\s+\w+\s*=\s*$"), "null;"),
    (re.compile(r"\bimport\s*$"), '{ example } from "./example";'),
    (re.compile(r"\bif\s*\(\s*$"), "condition) {\n    \n}"),
    (re.compile(r"\bfor\s*\(\s*$"), "let i = 0; i < n; i++) {\n    \n}"),
    (re.compile(r"\basync\s+function\s*$", re.M), "handler() {\n    \n}"),
    (re.compile(r"\bdef\s+\w+\s*\(\s*$"), "self):\n    pass"),
    (re.compile(r"\bclass\s+\w+\s*$"), ":\n    pass"),
    (re.compile(r"\.\s*$"), "findById(id);"),
    (re.compile(r"await\s+db\.\s*$"), "findUser(id);"),
    (re.compile(r"return\s+<div>\s*$"), "Hello</div>;"),
    (re.compile(r"SELECT\s+\*\s+FROM\s+\w+\s+WHERE\s+$", re.I), "id = ?;"),
]


def mock_completion(prefix: str, suffix: str, language: str) -> str:
    trimmed = prefix.rstrip()
    for pattern, completion in MOCK_RULES:
        if pattern.search(trimmed) or pattern.search(prefix):
            return completion
    last_line = prefix.split("\n")[-1] if prefix else ""
    if last_line.strip().endswith("("):
        return "arg) {\n    \n}"
    if language in {"typescript", "javascript", "typescriptreact", "javascriptreact"}:
        return "();"
    if language == "python":
        return "pass"
    return ""
