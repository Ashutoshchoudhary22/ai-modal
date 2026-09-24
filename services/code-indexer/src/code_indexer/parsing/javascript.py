"""JavaScript/JSX Tree-sitter extractor."""

from __future__ import annotations

import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

from code_indexer.models import ImportRecord, Symbol
from code_indexer.parsing.registry import LanguageParser, ParseResult, _node_text


class JavaScriptParser(LanguageParser):
    language_id = "javascript"

    def __init__(self) -> None:
        self._language = Language(tsjavascript.language())
        self._parser = Parser(self._language)

    def parse(
        self,
        *,
        workspace_id: str,
        file_path: str,
        source: str,
    ) -> ParseResult:
        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        symbols: list[Symbol] = []
        imports: list[ImportRecord] = []
        self._walk(tree.root_node, source_bytes, workspace_id, file_path, symbols, imports)
        return ParseResult(symbols=symbols, imports=imports, errors=[])

    def _walk(
        self,
        node,
        source: bytes,
        workspace_id: str,
        file_path: str,
        symbols: list[Symbol],
        imports: list[ImportRecord],
    ) -> None:
        if node.type in {"function_declaration", "method_definition", "arrow_function"}:
            name = self._extract_name(node, source)
            if name:
                symbols.append(
                    Symbol(
                        workspace_id=workspace_id,
                        file_path=file_path,
                        kind="function",
                        name=name,
                        qualified_name=name,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                    )
                )
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(source, name_node)
                symbols.append(
                    Symbol(
                        workspace_id=workspace_id,
                        file_path=file_path,
                        kind="class",
                        name=name,
                        qualified_name=name,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                    )
                )
        if node.type == "import_statement":
            source_node = node.child_by_field_name("source")
            module = _node_text(source, source_node).strip("'\"") if source_node else ""
            imports.append(
                ImportRecord(
                    workspace_id=workspace_id,
                    file_path=file_path,
                    module_path=module,
                    imported_name=None,
                    alias=None,
                    start_line=node.start_point[0] + 1,
                )
            )
        if node.type == "call_expression":
            func = node.child_by_field_name("function")
            if func and func.type == "identifier" and _node_text(source, func) == "require":
                args = node.child_by_field_name("arguments")
                if args and args.child_count > 0:
                    module = _node_text(source, args.children[0]).strip("'\"")
                    imports.append(
                        ImportRecord(
                            workspace_id=workspace_id,
                            file_path=file_path,
                            module_path=module,
                            imported_name=None,
                            alias=None,
                            start_line=node.start_point[0] + 1,
                        )
                    )
        for child in node.children:
            self._walk(child, source, workspace_id, file_path, symbols, imports)

    @staticmethod
    def _extract_name(node, source: bytes) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node:
            return _node_text(source, name_node)
        return None
