"""Repository intelligence tools."""

from __future__ import annotations

from typing import Any

from agent.config import ToolSettings, load_tool_settings
from agent.context import ToolExecutionContext
from agent.tools.base import BaseTool
from ai_platform_protocol.tools import ToolDefinition, ToolPermission, ToolResult
from code_indexer.config import IndexerConfig
from code_indexer.context import build_context
from code_indexer.loader import load_index_data
from code_indexer.search import lexical_search


class CodeSearchTool(BaseTool):
    definition = ToolDefinition(
        name="code.search",
        description="Search the indexed repository",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "search_mode": {"type": "string", "enum": ["lexical"]},
            },
            "required": ["query"],
        },
        permissions=[ToolPermission.READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        self._require_args(arguments, "query")
        query = arguments["query"].strip()
        if not query:
            return self._ok({"matches": [], "query": query})
        limit = min(int(arguments.get("limit", 20)), self._settings.max_search_results)
        _, symbols, _, contents = load_index_data(
            context.workspace_root,
            workspace_id=context.workspace_id,
        )
        results = lexical_search(query, symbols=symbols, file_contents=contents, limit=limit)
        matches = [
            {
                "file": r.relative_path,
                "line": r.line_start,
                "symbol": r.symbol_name,
                "score": r.final_score,
                "snippet": r.snippet[:500],
                "match_type": r.match_type,
            }
            for r in results
        ]
        return self._ok({"query": query, "matches": matches})


class CodeSymbolsTool(BaseTool):
    definition = ToolDefinition(
        name="code.symbols",
        description="List repository symbols",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "symbol_name": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
        },
        permissions=[ToolPermission.READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        limit = min(int(arguments.get("limit", 50)), self._settings.max_search_results)
        _, symbols, _, _ = load_index_data(
            context.workspace_root,
            workspace_id=context.workspace_id,
        )
        path_filter = arguments.get("path")
        name_filter = arguments.get("symbol_name")
        if path_filter:
            symbols = [s for s in symbols if s.file_path == path_filter.replace("\\", "/")]
        if name_filter:
            symbols = [s for s in symbols if name_filter.lower() in s.name.lower()]
        payload = [
            {
                "name": s.name,
                "kind": s.kind,
                "qualified_name": s.qualified_name,
                "file": s.file_path,
                "start_line": s.start_line,
                "end_line": s.end_line,
                "parent_symbol_id": s.parent_symbol_id,
            }
            for s in symbols[:limit]
        ]
        return self._ok({"symbols": payload, "count": len(payload)})


class CodeContextTool(BaseTool):
    definition = ToolDefinition(
        name="code.context",
        description="Build bounded repository context for a query",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_context_files": {"type": "integer"},
                "max_context_symbols": {"type": "integer"},
                "max_context_chars": {"type": "integer"},
            },
            "required": ["query"],
        },
        permissions=[ToolPermission.READ],
    )

    def __init__(self, settings: ToolSettings | None = None) -> None:
        self._settings = settings or load_tool_settings()

    async def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        self._require_args(arguments, "query")
        cfg = IndexerConfig(
            max_context_files=int(arguments.get("max_context_files", 10)),
            max_context_symbols=int(arguments.get("max_context_symbols", 20)),
            max_context_chars=min(
                int(arguments.get("max_context_chars", self._settings.max_context_chars)),
                self._settings.max_context_chars,
            ),
        )
        _, symbols, imports, contents = load_index_data(
            context.workspace_root,
            workspace_id=context.workspace_id,
        )
        ctx = build_context(
            arguments["query"],
            symbols=symbols,
            imports=imports,
            file_contents=contents,
            config=cfg,
        )
        return self._ok(
            {
                "query": ctx.query,
                "files": [f.relative_path for f in ctx.files],
                "symbols": [s.qualified_name for s in ctx.symbols],
                "snippets": [
                    {
                        "file": s.relative_path,
                        "line_start": s.line_start,
                        "line_end": s.line_end,
                        "symbol": s.symbol_name,
                        "snippet": s.snippet[:500],
                    }
                    for s in ctx.snippets
                ],
                "imports": [
                    {
                        "file": i.file_path,
                        "module": i.module_path,
                        "status": i.resolution_status,
                    }
                    for i in ctx.imports
                ],
            }
        )
