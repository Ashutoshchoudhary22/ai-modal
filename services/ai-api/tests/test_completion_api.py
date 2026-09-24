"""Completion API tests."""

from __future__ import annotations

from ai_api.dependencies import reset_dependencies
from ai_api.main import create_app
from fastapi.testclient import TestClient


def test_completion_mock_provider() -> None:
    reset_dependencies()
    client = TestClient(create_app())
    response = client.post(
        "/v1/completions",
        json={
            "file_path": "src/example.ts",
            "language": "typescript",
            "prefix": "const user = await db.",
            "suffix": "",
            "cursor": {"line": 0, "column": 22},
            "options": {"max_tokens": 64},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completion"]["text"]
    assert "findById" in data["completion"]["text"]


def test_completion_sensitive_file_blocked() -> None:
    reset_dependencies()
    client = TestClient(create_app())
    response = client.post(
        "/v1/completions",
        json={
            "file_path": ".env",
            "language": "plaintext",
            "prefix": "API_KEY=",
            "suffix": "",
            "cursor": {"line": 0, "column": 8},
        },
    )
    assert response.status_code == 403


def test_completion_sanitizes_response() -> None:
    from ai_api.completion.validation import sanitize_completion

    result = sanitize_completion("findById(id);", "await db.", "")
    assert result == "findById(id);"
