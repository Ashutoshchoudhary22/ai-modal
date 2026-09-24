# Repository Intelligence (Phase 4)

Static analysis pipeline for workspace scanning, Tree-sitter parsing, symbol extraction, lexical search, and context retrieval.

## Architecture

```text
Workspace → Scanner → Language Detection → Git Metadata → Tree-sitter
    → Symbols/Imports → Graph → MySQL (authoritative) + .code_index/ (cache)
    → Lexical/Hybrid Search → Context Builder
```

## Persistence

- **MySQL** — authoritative repository metadata (`repository_files`, `repository_symbols`, `repository_imports`, `repository_index_runs`)
- **Filesystem** — local cache at `<workspace>/.code_index/` (hashes, index snapshot, source files remain on disk)

Indexing writes to MySQL first; filesystem cache is updated only after MySQL persistence succeeds.

## Git metadata

Read-only Git queries (branch, commit, tracked/modified/untracked counts) via safe subprocess argument arrays. Git is optional — indexing works without it.

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

## API

```text
POST /v1/workspaces
POST /v1/workspaces/{id}/index
GET  /v1/workspaces/{id}/index/status
GET  /v1/workspaces/{id}/files
GET  /v1/workspaces/{id}/symbols
GET  /v1/workspaces/{id}/graph
POST /v1/workspaces/{id}/search
POST /v1/workspaces/{id}/context
```

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
