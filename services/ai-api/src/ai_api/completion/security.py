"""Completion request security."""

from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath

SENSITIVE_PATTERNS = [".env", ".pem", ".key", "credentials.", "secrets."]

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|password|secret|token|bearer)\s*[:=]\s*['\"]?\S+"),
    re.compile(r"(?i)-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def is_sensitive_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    basename = PurePosixPath(normalized).name
    if normalized.endswith(".env.example"):
        return False
    for pattern in SENSITIVE_PATTERNS:
        if pattern.endswith("."):
            if basename.startswith(pattern):
                return True
        elif fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(normalized, f"*/{pattern}"):
            return True
    return False


def redact_secrets(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def validate_path_in_workspace(file_path: str) -> None:
    normalized = file_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise ValueError("Path traversal rejected")
