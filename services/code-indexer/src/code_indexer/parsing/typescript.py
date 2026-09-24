"""TypeScript/TSX Tree-sitter extractor."""

from __future__ import annotations

import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser

from code_indexer.parsing.javascript import JavaScriptParser


class TypeScriptParser(JavaScriptParser):
    language_id = "typescript"

    def __init__(self) -> None:
        self._language = Language(tstypescript.language_typescript())
        self._parser = Parser(self._language)
