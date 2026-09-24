# Repository Intelligence (Phase 4)

Static analysis pipeline for workspace scanning, Tree-sitter parsing, symbol extraction, lexical search, and context retrieval.

## Architecture

```text
Workspace → Scanner → Language Detection → Tree-sitter → Symbols/Imports
    → Graph → Index Store → Lexical/Hybrid Search → Context Builder
```

## CLI

```bash
python -m code_indexer scan --workspace .
python -m code_indexer index --workspace .
python -m code_indexer search --workspace . --query "AuthService"
python -m code_indexer context --workspace . --query "auth"
python -m code_indexer symbols --workspace . --query "User"
```

## Supported parsers

- Python (`tree-sitter-python`)
- JavaScript / JSX (`tree-sitter-javascript`)
- TypeScript / TSX (`tree-sitter-typescript`)

## Index storage

- Local index: `<workspace>/.code_index/`
- MySQL metadata: `repository_index_runs`, `repository_symbols`, `repository_imports`

## Security

- Path traversal blocked
- Symlinks not followed during scan
- Sensitive files (`.env`, keys) ignored by default
- Static analysis only — no code execution

## Limitations

- Import resolution is heuristic, not full package resolution
- No call-graph analysis
- Semantic search requires configured `EmbeddingProvider`
- Parser coverage varies by language

See `services/code-indexer/README.md` for service details.
