"""Load persisted index data from a workspace."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from code_indexer.graph import RepositoryGraph
from code_indexer.indexer import RepositoryIndexer
from code_indexer.models import ImportRecord, RepositoryFile, Symbol


def load_index_data(
    workspace: Path,
    *,
    workspace_id: str | None = None,
) -> tuple[list[RepositoryFile], list[Symbol], list[ImportRecord], dict[str, str]]:
    indexer = RepositoryIndexer(workspace, workspace_id=workspace_id)
    data = indexer.store.load_index()
    if not data:
        return [], [], [], {}
    files = [RepositoryFile(**f) for f in data.get("files", [])]
    symbols = [Symbol(**s) for s in data.get("symbols", [])]
    imports = [ImportRecord(**i) for i in data.get("imports", [])]
    contents = _load_file_contents(workspace, files, symbols, imports)
    return files, symbols, imports, contents


def _load_file_contents(
    workspace: Path,
    files: list[RepositoryFile],
    symbols: list[Symbol],
    imports: list[ImportRecord],
) -> dict[str, str]:
    contents: dict[str, str] = {}
    paths = {f.relative_path for f in files}
    paths.update(s.file_path for s in symbols)
    paths.update(i.file_path for i in imports)
    for relative_path in sorted(paths):
        path = workspace / relative_path
        if path.exists() and relative_path not in contents:
            contents[relative_path] = path.read_text(encoding="utf-8", errors="replace")
    return contents


def build_graph_from_index(
    files: list[RepositoryFile],
    symbols: list[Symbol],
    imports: list[ImportRecord],
) -> RepositoryGraph:
    graph = RepositoryGraph()
    for repo_file in sorted(files, key=lambda f: f.relative_path):
        graph.add_file(repo_file.file_id, repo_file.relative_path)
    for symbol in sorted(symbols, key=lambda s: s.id):
        graph.add_symbol(symbol)
    for imp in sorted(imports, key=lambda i: i.id):
        graph.add_import(imp.file_path, imp)
    return graph


def graph_to_dict(graph: RepositoryGraph) -> dict:
    return {
        "nodes": dict(sorted(graph.nodes.items())),
        "edges": [
            asdict(edge)
            for edge in sorted(
                graph.edges,
                key=lambda edge: (edge.edge_type, edge.source_id, edge.target_id),
            )
        ],
    }
