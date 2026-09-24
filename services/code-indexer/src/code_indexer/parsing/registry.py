"""Tree-sitter parser registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from code_indexer.models import ImportRecord, Symbol


@dataclass
class ParseResult:
    symbols: list[Symbol]
    imports: list[ImportRecord]
    errors: list[str]


class LanguageParser:
    language_id: str

    def parse(
        self,
        *,
        workspace_id: str,
        file_path: str,
        source: str,
    ) -> ParseResult:
        raise NotImplementedError


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, LanguageParser] = {}

    def register(self, parser: LanguageParser) -> None:
        self._parsers[parser.language_id] = parser

    def parse_file(
        self,
        *,
        language_id: str,
        workspace_id: str,
        file_path: str,
        source: str,
    ) -> ParseResult:
        parser = self._parsers.get(language_id)
        if parser is None:
            return ParseResult(symbols=[], imports=[], errors=["no parser registered"])
        try:
            return parser.parse(
                workspace_id=workspace_id,
                file_path=file_path,
                source=source,
            )
        except Exception as exc:
            return ParseResult(symbols=[], imports=[], errors=[str(exc)])


def _node_text(source: bytes, node: Any) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def build_default_registry() -> ParserRegistry:
    from code_indexer.parsing.javascript import JavaScriptParser
    from code_indexer.parsing.python import PythonParser
    from code_indexer.parsing.typescript import TypeScriptParser

    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(JavaScriptParser())
    registry.register(TypeScriptParser())
    return registry
