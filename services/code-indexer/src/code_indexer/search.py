"""Lexical repository search."""

from __future__ import annotations

import re

from code_indexer.models import SearchResult, Symbol


def _query_tokens(query: str) -> list[str]:
    return [token for token in re.split(r"\W+", query.lower()) if len(token) >= 3]


def lexical_search(
    query: str,
    *,
    symbols: list[Symbol],
    file_contents: dict[str, str],
    limit: int = 20,
) -> list[SearchResult]:
    query_lower = query.lower()
    tokens = _query_tokens(query)
    results: list[SearchResult] = []

    for symbol in symbols:
        score = 0.0
        match_type = "text"
        if symbol.name.lower() == query_lower:
            score = 100.0
            match_type = "exact_symbol"
        elif query_lower in symbol.name.lower():
            score = 80.0
            match_type = "symbol_name"
        elif query_lower in symbol.qualified_name.lower():
            score = 60.0
            match_type = "symbol_name"
        elif any(token in symbol.name.lower() for token in tokens):
            score = 55.0
            match_type = "symbol_name"
        else:
            continue
        snippet = _extract_snippet(
            file_contents.get(symbol.file_path, ""),
            symbol.start_line,
            symbol.end_line,
        )
        results.append(
            SearchResult(
                file_id=symbol.file_path,
                relative_path=symbol.file_path,
                symbol_id=symbol.id,
                symbol_name=symbol.name,
                line_start=symbol.start_line,
                line_end=symbol.end_line,
                snippet=snippet,
                match_type=match_type,
                lexical_score=score,
                final_score=score,
            )
        )

    for path, content in sorted(file_contents.items()):
        path_lower = path.lower()
        token_hit = any(token in path_lower for token in tokens)
        if query_lower == path_lower or query_lower in path_lower or token_hit:
            score = 90.0 if query_lower == path_lower else 50.0 if token_hit else 45.0
            results.append(
                SearchResult(
                    file_id=path,
                    relative_path=path,
                    symbol_id=None,
                    symbol_name=None,
                    line_start=1,
                    line_end=min(5, content.count("\n") + 1),
                    snippet=_extract_snippet(content, 1, 5),
                    match_type="path",
                    lexical_score=score,
                    final_score=score,
                )
            )
        elif query_lower in content.lower():
            line = _find_line(content, query_lower)
            results.append(
                SearchResult(
                    file_id=path,
                    relative_path=path,
                    symbol_id=None,
                    symbol_name=None,
                    line_start=line,
                    line_end=line + 3,
                    snippet=_extract_snippet(content, line, line + 3),
                    match_type="text",
                    lexical_score=30.0,
                    final_score=30.0,
                )
            )

    results.sort(key=lambda r: (-r.lexical_score, r.relative_path, r.line_start))
    return results[:limit]


def _extract_snippet(content: str, start_line: int, end_line: int, max_chars: int = 500) -> str:
    lines = content.splitlines()
    start = max(0, start_line - 1)
    end = min(len(lines), end_line)
    snippet = "\n".join(lines[start:end])
    return snippet[:max_chars]


def _find_line(content: str, query_lower: str) -> int:
    for index, line in enumerate(content.splitlines(), start=1):
        if query_lower in line.lower():
            return index
    return 1
