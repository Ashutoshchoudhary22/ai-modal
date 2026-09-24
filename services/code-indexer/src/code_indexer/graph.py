"""Repository graph builder."""

from __future__ import annotations

from dataclasses import dataclass, field

from code_indexer.models import GraphEdge, ImportRecord, Symbol


@dataclass
class RepositoryGraph:
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_file(self, file_id: str, path: str) -> None:
        self.nodes[file_id] = {"type": "file", "path": path}

    def add_symbol(self, symbol: Symbol) -> None:
        self.nodes[symbol.id] = {
            "type": "symbol",
            "kind": symbol.kind,
            "name": symbol.name,
            "qualified_name": symbol.qualified_name,
            "file_path": symbol.file_path,
        }
        self.edges.append(
            GraphEdge(
                source_id=symbol.file_path,
                target_id=symbol.id,
                edge_type="defines",
            )
        )
        if symbol.parent_symbol_id:
            self.edges.append(
                GraphEdge(
                    source_id=symbol.parent_symbol_id,
                    target_id=symbol.id,
                    edge_type="child_of",
                )
            )

    def add_import(self, file_id: str, imp: ImportRecord) -> None:
        self.edges.append(
            GraphEdge(
                source_id=file_id,
                target_id=imp.resolved_path or imp.module_path,
                edge_type="imports",
                metadata={"status": imp.resolution_status},
            )
        )
