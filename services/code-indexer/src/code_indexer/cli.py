"""Repository intelligence CLI."""

from __future__ import annotations

import argparse
import json
import sys

from code_indexer.context import build_context
from code_indexer.indexer import RepositoryIndexer
from code_indexer.loader import build_graph_from_index, graph_to_dict, load_index_data
from code_indexer.scanner import WorkspaceScanner
from code_indexer.search import lexical_search
from code_indexer.security import resolve_workspace_path


def cmd_scan(args: argparse.Namespace) -> int:
    scanner = WorkspaceScanner(args.workspace)
    files, stats = scanner.scan()
    output = {
        "discovered": stats.discovered,
        "ignored": stats.ignored,
        "binary": stats.binary,
        "supported": stats.supported,
        "files": [f.relative_path for f in files if not f.is_ignored],
    }
    print(json.dumps(output, indent=2) if args.json else _format_scan(stats, files))
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    indexer = RepositoryIndexer(args.workspace)
    run, stats = indexer.index(incremental=not args.full)
    output = {
        "run_id": run.run_id,
        "status": run.status,
        "stats": stats.__dict__,
    }
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(_format_index_stats(stats))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    indexer = RepositoryIndexer(args.workspace)
    data = indexer.store.load_index()
    if not data:
        print("No index found.")
        return 1
    run = data.get("run", {})
    print(json.dumps(run, indent=2) if args.json else json.dumps(run, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    _, symbols, _, contents = load_index_data(root)
    results = lexical_search(args.query, symbols=symbols, file_contents=contents, limit=args.limit)
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
    else:
        for result in results:
            print(f"{result.relative_path}:{result.line_start} score={result.final_score:.1f}")
            print(result.snippet[:200])
            print("---")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    _, symbols, imports, contents = load_index_data(root)
    ctx = build_context(args.query, symbols=symbols, imports=imports, file_contents=contents)
    if args.json:
        print(
            json.dumps(
                {
                    "query": ctx.query,
                    "files": [f.relative_path for f in ctx.files],
                    "symbols": [s.qualified_name for s in ctx.symbols],
                    "snippets": [s.snippet for s in ctx.snippets],
                },
                indent=2,
            )
        )
    else:
        print(f"Query: {ctx.query}")
        for snippet in ctx.snippets:
            print(f"- {snippet.relative_path}:{snippet.line_start} {snippet.symbol_name or ''}")
    return 0


def cmd_symbols(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    _, symbols, _, _ = load_index_data(root)
    if args.query:
        symbols = [s for s in symbols if args.query.lower() in s.name.lower()]
    if args.json:
        print(json.dumps([s.__dict__ for s in symbols], indent=2))
    else:
        for sym in symbols:
            print(f"{sym.file_path}:{sym.start_line} {sym.kind} {sym.qualified_name}")
    return 0


def cmd_files(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    files, _, _, _ = load_index_data(root)
    if args.json:
        print(json.dumps([f.__dict__ for f in files], indent=2))
    else:
        for repo_file in files:
            print(f"{repo_file.relative_path} lang={repo_file.language or '-'}")
    return 0


def cmd_imports(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    _, _, imports, _ = load_index_data(root)
    if args.query:
        imports = [i for i in imports if args.query.lower() in i.module_path.lower()]
    if args.json:
        print(json.dumps([i.__dict__ for i in imports], indent=2))
    else:
        for imp in imports:
            print(
                f"{imp.file_path}:{imp.start_line} {imp.module_path} status={imp.resolution_status}"
            )
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    root = resolve_workspace_path(args.workspace)
    files, symbols, imports, _ = load_index_data(root)
    graph = build_graph_from_index(files, symbols, imports)
    payload = graph_to_dict(graph)
    print(json.dumps(payload, indent=2) if args.json else json.dumps(payload, indent=2))
    return 0


def _format_scan(stats, files) -> str:
    return (
        f"Discovered: {stats.discovered}\n"
        f"Ignored: {stats.ignored}\n"
        f"Binary: {stats.binary}\n"
        f"Supported: {stats.supported}\n"
        f"Text files: {len([f for f in files if not f.is_binary and not f.is_ignored])}"
    )


def _format_index_stats(stats) -> str:
    return (
        f"Files discovered: {stats.files_discovered}\n"
        f"Ignored: {stats.ignored}\n"
        f"Binary: {stats.binary}\n"
        f"Supported source files: {stats.supported}\n\n"
        f"Indexed: {stats.indexed}\n"
        f"Skipped unchanged: {stats.skipped_unchanged}\n"
        f"Failed: {stats.failed}\n\n"
        f"Symbols: {stats.symbols}\n"
        f"Imports: {stats.imports}\n"
        f"Resolved local imports: {stats.resolved_imports}\n"
        f"Unresolved imports: {stats.unresolved_imports}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Platform repository intelligence")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("--workspace", default=".")
    scan.set_defaults(func=cmd_scan)

    index = sub.add_parser("index")
    index.add_argument("--workspace", default=".")
    index.add_argument("--full", action="store_true", help="Full re-index")
    index.set_defaults(func=cmd_index)

    status = sub.add_parser("status")
    status.add_argument("--workspace", default=".")
    status.set_defaults(func=cmd_status)

    search = sub.add_parser("search")
    search.add_argument("--workspace", default=".")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=cmd_search)

    context = sub.add_parser("context")
    context.add_argument("--workspace", default=".")
    context.add_argument("--query", required=True)
    context.set_defaults(func=cmd_context)

    symbols = sub.add_parser("symbols")
    symbols.add_argument("--workspace", default=".")
    symbols.add_argument("--query", default=None)
    symbols.set_defaults(func=cmd_symbols)

    files = sub.add_parser("files")
    files.add_argument("--workspace", default=".")
    files.set_defaults(func=cmd_files)

    imports = sub.add_parser("imports")
    imports.add_argument("--workspace", default=".")
    imports.add_argument("--query", default=None)
    imports.set_defaults(func=cmd_imports)

    graph = sub.add_parser("graph")
    graph.add_argument("--workspace", default=".")
    graph.set_defaults(func=cmd_graph)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
