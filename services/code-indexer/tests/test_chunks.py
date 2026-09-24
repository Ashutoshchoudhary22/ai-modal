"""Structural chunking tests."""

from __future__ import annotations

from code_indexer.chunks import build_chunks
from code_indexer.config import IndexerConfig
from code_indexer.models import Symbol


def _symbol(name: str, kind: str, start: int, end: int, path: str = "src/a.py") -> Symbol:
    return Symbol(
        workspace_id="ws",
        file_path=path,
        kind=kind,
        name=name,
        qualified_name=name,
        start_line=start,
        end_line=end,
    )


def test_function_and_class_chunks():
    content = "class User:\n    def greet(self):\n        return 'hi'\n\ndef top():\n    pass\n"
    symbols = [
        _symbol("User", "class", 1, 3),
        _symbol("greet", "method", 2, 3),
        _symbol("top", "function", 5, 6),
    ]
    chunks = build_chunks(symbols, {"src/a.py": content})
    assert len(chunks) == 3
    assert chunks[0].content.startswith("class User")
    assert chunks[2].content.strip() == "def top():\n    pass"


def test_large_symbol_truncated_deterministically():
    lines = ["def big():"] + ["    x = 1"] * 500
    content = "\n".join(lines)
    symbols = [_symbol("big", "function", 1, len(lines))]
    cfg = IndexerConfig(max_chunk_chars=80)
    chunks = build_chunks(symbols, {"src/a.py": content}, config=cfg)
    assert len(chunks) == 1
    assert len(chunks[0].content) <= 80
    first_id = chunks[0].chunk_id
    second = build_chunks(symbols, {"src/a.py": content}, config=cfg)
    assert second[0].chunk_id == first_id


def test_nested_symbol_chunks_preserve_lines():
    content = "class Outer:\n    class Inner:\n        pass\n"
    symbols = [
        _symbol("Outer", "class", 1, 3),
        _symbol("Inner", "class", 2, 3),
    ]
    chunks = build_chunks(symbols, {"src/a.py": content})
    assert "class Inner" in chunks[1].content
