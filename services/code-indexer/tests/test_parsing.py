from code_indexer.parsing import build_default_registry


def test_python_parser_extracts_function():
    registry = build_default_registry()
    source = "def hello():\n    return 1\n"
    result = registry.parse_file(
        language_id="python",
        workspace_id="ws",
        file_path="hello.py",
        source=source,
    )
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "hello"


def test_typescript_parser_extracts_class():
    registry = build_default_registry()
    source = "export class AuthService {\n  login() {}\n}\n"
    result = registry.parse_file(
        language_id="typescript",
        workspace_id="ws",
        file_path="service.ts",
        source=source,
    )
    names = {s.name for s in result.symbols}
    assert "AuthService" in names
