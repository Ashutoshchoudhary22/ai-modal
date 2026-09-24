"""Import resolver unit tests."""

from __future__ import annotations

from code_indexer.imports.resolve import resolve_imports
from code_indexer.models import ImportRecord


def _import(module_path: str, file_path: str = "src/main.ts") -> ImportRecord:
    return ImportRecord(
        workspace_id="ws",
        file_path=file_path,
        module_path=module_path,
        imported_name=None,
        alias=None,
        start_line=1,
    )


def test_resolve_relative_file_and_index():
    known = {
        "src/models/User.ts",
        "src/auth/index.ts",
        "src/auth/service.ts",
        "pkg/foo.py",
        "pkg/__init__.py",
    }
    results = resolve_imports(
        [
            _import("./models/User"),
            _import("./auth"),
            _import("../pkg/foo", "src/main.py"),
        ],
        file_path="src/main.ts",
        known_paths=known,
    )
    assert results[0].resolution_status == "resolved_local"
    assert results[0].resolved_path == "src/models/User.ts"
    assert results[1].resolved_path == "src/auth/index.ts"
    assert results[2].resolved_path == "pkg/foo.py"


def test_unresolved_and_external():
    known = {"src/a.ts"}
    unresolved = resolve_imports([_import("./missing")], file_path="src/a.ts", known_paths=known)
    assert unresolved[0].resolution_status == "unresolved_local"
    external = resolve_imports([_import("react")], file_path="src/a.ts", known_paths=known)
    assert external[0].resolution_status == "external"
