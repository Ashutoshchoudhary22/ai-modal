"""Workspace indexing and search routes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from code_indexer.config import IndexerConfig
from code_indexer.context import build_context
from code_indexer.git_info import get_git_metadata
from code_indexer.indexer import RepositoryIndexer
from code_indexer.loader import build_graph_from_index, graph_to_dict, load_index_data
from code_indexer.search import lexical_search
from code_indexer.security import PathSecurityError
from code_indexer.services.workspace_service import WorkspaceService

router = APIRouter()
_service = WorkspaceService()


class CreateWorkspaceBody(BaseModel):
    name: str
    root_path: str
    team_id: str | None = None


class IndexBody(BaseModel):
    root_path: str | None = None
    force: bool = False


class SearchBody(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=100)


class ContextBody(BaseModel):
    query: str


def _resolve_root(workspace_id: str, root_path: str | None) -> Path:
    try:
        return _service.resolve_root_path(workspace_id, fallback_root=root_path)
    except PathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workspaces")
async def create_workspace(body: CreateWorkspaceBody) -> dict:
    try:
        record = _service.create_workspace(
            name=body.name,
            root_path=body.root_path,
            team_id=body.team_id,
        )
    except PathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    return asdict(record)


@router.post("/workspaces/{workspace_id}/index")
async def index_workspace(workspace_id: str, body: IndexBody) -> dict:
    root = _resolve_root(workspace_id, body.root_path)
    if not root.exists():
        raise HTTPException(status_code=404, detail="Workspace path not found")
    config = IndexerConfig()
    indexer = RepositoryIndexer(root, workspace_id=workspace_id, config=config)
    try:
        run, stats = indexer.index(incremental=not body.force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    git = get_git_metadata(root)
    return {
        "run_id": run.run_id,
        "status": run.status,
        "stats": stats.__dict__,
        "git": asdict(git),
    }


@router.get("/workspaces/{workspace_id}/index/status")
async def index_status(
    workspace_id: str,
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
) -> dict:
    root = _resolve_root(workspace_id, root_path)
    indexer = RepositoryIndexer(root, workspace_id=workspace_id, config=IndexerConfig())
    data = indexer.store.load_index()
    if not data:
        raise HTTPException(status_code=404, detail="Index not found")
    payload = dict(data.get("run", {}))
    payload["git"] = asdict(get_git_metadata(root))
    return payload


@router.get("/workspaces/{workspace_id}/files")
async def list_files(
    workspace_id: str,
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
) -> dict:
    root = _resolve_root(workspace_id, root_path)
    files, _, _, _ = load_index_data(root, workspace_id=workspace_id)
    if not files:
        raise HTTPException(status_code=404, detail="Index not found")
    return {"files": [asdict(f) for f in files]}


@router.get("/workspaces/{workspace_id}/symbols")
async def list_symbols(
    workspace_id: str,
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
    query: str | None = None,
) -> dict:
    root = _resolve_root(workspace_id, root_path)
    _, symbols, _, _ = load_index_data(root, workspace_id=workspace_id)
    if not symbols and not Path(root / ".code_index" / "index.json").exists():
        raise HTTPException(status_code=404, detail="Index not found")
    if query:
        symbols = [s for s in symbols if query.lower() in s.name.lower()]
    return {"symbols": [asdict(s) for s in symbols]}


@router.get("/workspaces/{workspace_id}/graph")
async def get_graph(
    workspace_id: str,
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
) -> dict:
    root = _resolve_root(workspace_id, root_path)
    files, symbols, imports, _ = load_index_data(root, workspace_id=workspace_id)
    if not files and not Path(root / ".code_index" / "index.json").exists():
        raise HTTPException(status_code=404, detail="Index not found")
    graph = build_graph_from_index(files, symbols, imports)
    return graph_to_dict(graph)


@router.post("/workspaces/{workspace_id}/search")
async def search_workspace(
    workspace_id: str,
    body: SearchBody,
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
) -> dict:
    root = _resolve_root(workspace_id, root_path)
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
    root_path: str | None = Query(default=None, description="Workspace root path fallback"),
) -> dict:
    root = _resolve_root(workspace_id, root_path)
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
