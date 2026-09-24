# Web Test Console

Minimal React + Vite UI for exercising the AI API during development.

## Prerequisites

- AI API running (default `http://localhost:8000`)
- Node.js 20+

## Run

```bash
# From repository root
npm install
npm run dev:web
```

Open http://localhost:5173

## Fallback (no npm)

Open `apps/web/test-console.html` in a browser while the AI API is running.

## Status

**IMPLEMENTED (dev tool):** health, ready, chat, streaming, embeddings, models list.
