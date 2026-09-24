# Desktop IDE (Phase 13)

The AI Platform Desktop IDE is an Electron orchestration layer over existing platform services.

## Architecture

```
Renderer (React + Monaco)
        ↓ preload bridge (contextIsolation)
Main Process (workspace, fs, terminal, git)
        ↓ HTTP
┌───────────────┬────────────────┬─────────────────┐
│ AI API :8000  │ Agent :8001    │ Indexer :8002   │
│ chat/stream   │ agent/tools/ui  │ search/symbols  │
│ multimodal    │ browser/eval    │ context         │
└───────────────┴────────────────┴─────────────────┘
```

## Security

- Renderer has **no** Node.js `fs`, `child_process`, or `require`
- All privileged operations go through typed `window.desktop` preload API
- Filesystem scoped to workspace root with path traversal and sensitive-file protection
- Terminal commands validated (no metacharacters, denied destructive commands)
- Backend agent/browser/terminal policies remain authoritative over UI approval

## Workspace Lifecycle

1. User selects folder via **Open Folder**
2. Main process validates path and starts file watcher
3. Code indexer workspace created and indexed (async)
4. Git branch detected (read-only)
5. On close: watcher stopped, terminals killed, context cleared

## Panels

| Panel | Backend |
|-------|---------|
| File Explorer | Preload filesystem API |
| Monaco Editor | Preload read/write |
| AI Chat | AI API `/v1/chat/stream` |
| Agent Mode | Agent `/v1/agent/runs/stream` |
| Terminal | Main process (policy-controlled) |
| Git | Main process `git` read commands |
| Problems | Agent `code.diagnostics` tool |
| Evaluation | Agent `/v1/evaluations/*` |
| UI Generation | Agent `/v1/ui/generate/stream` |
| Screenshot-to-Code | Agent `/v1/ui/screenshot-to-code/stream` |
| Browser Agent | Agent `/v1/browser/runs/stream` |

## Diff Review

AI/agent/UI proposed changes go through diff review before file write. User must Accept or Reject.

## Development

```bash
npm run dev:desktop
```

## Build / Packaging

```bash
npm run build:desktop
npm run package:desktop
```

Development packaging targets Windows, Linux, macOS (unsigned).

## Limitations

- No continuous inline completion (Phase 14)
- No SaaS authentication (Phase 16)
- No model routing (Phase 17)
- Single active workspace
- Process-level terminal isolation (not container)
- Evaluation requires training package mounted on agent service
