"""Workspace indexing and search routes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from code_indexer.context import build_context
from code_indexer.indexer import RepositoryIndexer
from code_indexer.loader import build_graph_from_index, graph_to_dict, load_index_data
from code_indexer.search import lexical_search
from code_indexer.security import resolve_workspace_path

router = APIRouter()


class IndexBody(BaseModel):
    root_path: str
    force: bool = False


class SearchBody(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=100)


class ContextBody(BaseModel):
    query: str


def _resolve_root(root_path: str) -> Path:
    try:
        return resolve_workspace_path(root_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workspaces/{workspace_id}/index")
async def index_workspace(workspace_id: str, body: IndexBody) -> dict:
    root = _resolve_root(body.root_path)
    if not root.exists():
        raise HTTPException(status_code=404, detail="Workspace path not found")
    indexer = RepositoryIndexer(root, workspace_id=workspace_id)
    run, stats = indexer.index(incremental=not body.force)
    return {"run_id": run.run_id, "status": run.status, "stats": stats.__dict__}


@router.get("/workspaces/{workspace_id}/index/status")
async def index_status(
    workspace_id: str,
    root_path: str = Query(..., description="Workspace root path"),
) -> dict:
    root = _resolve_root(root_path)
    indexer = RepositoryIndexer(root, workspace_id=workspace_id)
    data = indexer.store.load_index()
    if not data:
        raise HTTPException(status_code=404, detail="Index not found")
    return data.get("run", {})


@router.get("/workspaces/{workspace_id}/files")
async def list_files(
    workspace_id: str,
    root_path: str = Query(..., description="Workspace root path"),
) -> dict:
    root = _resolve_root(root_path)
    files, _, _, _ = load_index_data(root, workspace_id=workspace_id)
    if not files:
        raise HTTPException(status_code=404, detail="Index not found")
    return {"files": [asdict(f) for f in files]}


@router.get("/workspaces/{workspace_id}/symbols")
async def list_symbols(
    workspace_id: str,
    root_path: str = Query(..., description="Workspace root path"),
    query: str | None = None,
) -> dict:
    root = _resolve_root(root_path)
    _, symbols, _, _ = load_index_data(root, workspace_id=workspace_id)
    if not symbols and not Path(root / ".code_index" / "index.json").exists():
        raise HTTPException(status_code=404, detail="Index not found")
    if query:
        symbols = [s for s in symbols if query.lower() in s.name.lower()]
    return {"symbols": [asdict(s) for s in symbols]}


@router.get("/workspaces/{workspace_id}/graph")
async def get_graph(
    workspace_id: str,
    root_path: str = Query(..., description="Workspace root path"),
) -> dict:
    root = _resolve_root(root_path)
    files, symbols, imports, _ = load_index_data(root, workspace_id=workspace_id)
    if not files and not Path(root / ".code_index" / "index.json").exists():
        raise HTTPException(status_code=404, detail="Index not found")
    graph = build_graph_from_index(files, symbols, imports)
    return graph_to_dict(graph)


@router.post("/workspaces/{workspace_id}/search")
async def search_workspace(
    workspace_id: str,
    body: SearchBody,
    root_path: str = Query(..., description="Workspace root path"),
) -> dict:
    root = _resolve_root(root_path)
    _, symbols, _, contents = load_index_data(root, workspace_id=workspace_id)
    if not contents:
        raise HTTPException(status_code=404, detail="Index not found")
    results = lexical_search(
        body.query,
        symbols=symbols,
        file_contents=contents,
        limit=body.limit,
    )
    return {"results": [asdict(r) for r in results]}


@router.post("/workspaces/{workspace_id}/context")
async def context_workspace(
    workspace_id: str,
    body: ContextBody,
    root_path: str = Query(..., description="Workspace root path"),
) -> dict:
    root = _resolve_root(root_path)
    _, symbols, imports, contents = load_index_data(root, workspace_id=workspace_id)
    if not contents:
        raise HTTPException(status_code=404, detail="Index not found")
    ctx = build_context(body.query, symbols=symbols, imports=imports, file_contents=contents)
    return {
        "query": ctx.query,
        "files": [asdict(f) for f in ctx.files],
        "symbols": [asdict(s) for s in ctx.symbols],
        "snippets": [asdict(s) for s in ctx.snippets],
        "imports": [asdict(i) for i in ctx.imports],
    }
