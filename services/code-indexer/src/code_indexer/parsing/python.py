"""Python Tree-sitter extractor."""

from __future__ import annotations

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from code_indexer.models import ImportRecord, Symbol
from code_indexer.parsing.registry import LanguageParser, ParseResult, _node_text


class PythonParser(LanguageParser):
    language_id = "python"

    def __init__(self) -> None:
        self._language = Language(tspython.language())
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
        self._walk(
            tree.root_node,
            source_bytes,
            workspace_id,
            file_path,
            parent_qname=None,
            parent_id=None,
            symbols=symbols,
            imports=imports,
        )
        return ParseResult(symbols=symbols, imports=imports, errors=[])

    def _walk(
        self,
        node,
        source: bytes,
        workspace_id: str,
        file_path: str,
        parent_qname: str | None,
        parent_id: str | None,
        symbols: list[Symbol],
        imports: list[ImportRecord],
    ) -> None:
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(source, name_node)
                qname = f"{parent_qname}.{name}" if parent_qname else name
                sym = Symbol(
                    workspace_id=workspace_id,
                    file_path=file_path,
                    kind="method" if parent_qname else "function",
                    name=name,
                    qualified_name=qname,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_symbol_id=parent_id,
                )
                symbols.append(sym)
                for child in node.children:
                    self._walk(
                        child,
                        source,
                        workspace_id,
                        file_path,
                        qname,
                        sym.id,
                        symbols,
                        imports,
                    )
                return
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _node_text(source, name_node)
                qname = f"{parent_qname}.{name}" if parent_qname else name
                sym = Symbol(
                    workspace_id=workspace_id,
                    file_path=file_path,
                    kind="class",
                    name=name,
                    qualified_name=qname,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_symbol_id=parent_id,
                )
                symbols.append(sym)
                for child in node.children:
                    self._walk(
                        child,
                        source,
                        workspace_id,
                        file_path,
                        qname,
                        sym.id,
                        symbols,
                        imports,
                    )
                return
        if node.type in {"import_statement", "import_from_statement"}:
            line = node.start_point[0] + 1
            text = _node_text(source, node)
            imports.append(
                ImportRecord(
                    workspace_id=workspace_id,
                    file_path=file_path,
                    module_path=text,
                    imported_name=None,
                    alias=None,
                    start_line=line,
                )
            )
        for child in node.children:
            self._walk(
                child,
                source,
                workspace_id,
                file_path,
                parent_qname,
                parent_id,
                symbols,
                imports,
            )
