# AI Platform Desktop IDE

Electron + React + TypeScript + Monaco desktop developer environment (Phase 13).

## Development

Prerequisites: Node 20+, running AI Platform services.

```bash
# From repo root
npm install

# Start backend services (separate terminals)
make dev-ai-api          # :8000
cd services/agent && uvicorn agent.main:app --reload --port 8001
cd services/code-indexer && uvicorn code_indexer.main:app --reload --port 8002

# Start desktop
npm run dev:desktop
```

## Build

```bash
npm run build:desktop
npm run package:desktop   # development packaging (no signing)
```

## Security

- `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`
- Renderer accesses filesystem/terminal/git only via typed preload bridge
- Workspace-scoped path validation mirrors Phase 5 rules
- Sensitive files (.env, .pem, .key) blocked

## Configuration

Environment variables (see root `.env.example`):

- `AI_PLATFORM_DESKTOP_API_URL` — AI API URL (default `http://127.0.0.1:8000`)
- `AI_PLATFORM_AGENT_URL` — Agent service URL (default `http://127.0.0.1:8001`)
- `AI_PLATFORM_INDEXER_URL` — Code indexer URL (default `http://127.0.0.1:8002`)
- `AI_PLATFORM_DESKTOP_DEVTOOLS` — Open DevTools in development (`true`/`false`)
