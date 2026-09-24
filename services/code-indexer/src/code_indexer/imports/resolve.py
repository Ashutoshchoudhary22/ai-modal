"""Deterministic local import resolution."""

from __future__ import annotations

from pathlib import PurePosixPath
from posixpath import normpath

from code_indexer.models import ImportRecord

RESOLVABLE_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    "/__init__.py",
    "/index.js",
    "/index.ts",
    "/index.jsx",
    "/index.tsx",
)


def resolve_imports(
    imports: list[ImportRecord],
    *,
    file_path: str,
    known_paths: set[str],
) -> list[ImportRecord]:
    resolved: list[ImportRecord] = []
    base_dir = PurePosixPath(file_path).parent
    for record in imports:
        module = record.module_path.strip()
        if module.startswith("from ") or module.startswith("import "):
            module = _normalize_python_import(module)
        is_relative = (
            module.startswith("./")
            or module.startswith("../")
            or module.startswith(".")
            or "/" in module
        )
        if is_relative:
            candidate = normpath((base_dir / module).as_posix()).lstrip("/")
            target = _resolve_local(candidate, known_paths)
            if target:
                record.resolution_status = "resolved_local"
                record.resolved_path = target
            else:
                record.resolution_status = "unresolved_local"
        elif "." not in module and not module.startswith("/"):
            record.resolution_status = "external"
        else:
            record.resolution_status = "unknown"
        resolved.append(record)
    return resolved


def _normalize_python_import(text: str) -> str:
    if text.startswith("from "):
        parts = text.replace("from ", "").split(" import ")
        return parts[0].strip()
    if text.startswith("import "):
        return text.replace("import ", "").split(" as ")[0].strip().split(",")[0].strip()
    return text


def _resolve_local(candidate: str, known_paths: set[str]) -> str | None:
    normalized = candidate.replace("\\", "/")
    if normalized in known_paths:
        return normalized
    for ext in (".ts", ".tsx", ".js", ".jsx", ".py"):
        if f"{normalized}{ext}" in known_paths:
            return f"{normalized}{ext}"
    for suffix in ("/index.ts", "/index.js", "/index.tsx", "/index.jsx", "/__init__.py"):
        if f"{normalized}{suffix}" in known_paths:
            return f"{normalized}{suffix}"
    return None
