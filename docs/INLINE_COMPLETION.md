# Inline Code Completion (Phase 14) — GREEN

Copilot-style inline code completion for the AI Platform Desktop IDE.

**Status:** Phase 14 verified **GREEN** via real Electron + Playwright E2E (`npm run verify:completion` — 25/25 checks).

## Architecture

```
Monaco Editor
      ↓
MonacoInlineCompletionProvider
      ↓
CompletionController
      ↓
CompletionContextCollector
      ↓
POST /v1/completions (AI API)
      ↓
CompletionService → ModelProvider
      ↓
validation / sanitization
      ↓
Monaco ghost text
```

## Request Lifecycle

1. User types or presses `Ctrl+Space`
2. Debounce (default 250ms, configurable)
3. Collect prefix/suffix from the **current Monaco model** (unsaved buffer)
4. Optionally attach bounded repository context from the code indexer
5. POST to `POST /v1/completions` (non-streaming)
6. Validate response (stale check, sanitization)
7. Display as Monaco inline suggestion (ghost text)
8. `Tab` to accept, `Esc` to reject

## API

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/v1/completions` | POST | Synchronous completion (default) |

There is **no** `POST /v1/completions/stream` endpoint in this phase.

## Security

- Sensitive files (`.env`, `.env.local`, `credentials.*`, `secrets.*`, `*.pem`, `*.key`) blocked client- and server-side
- Workspace path validation on server
- Secret redaction before external provider calls
- No full repository upload — bounded context only (max ~5 symbols, ~3 file paths, ~4000 chars)
- Stale response protection via `requestId`, `documentVersion`, `cursorKey`, `filePath`, `invalidationGeneration`
- In-flight cancellation on typing, tab switch, workspace switch, cursor move, editor disposal

## Configuration

See `.env.example` for `AI_PLATFORM_COMPLETION_*` variables.

Desktop settings: **Assistant → Completion** tab.

| Setting | Purpose |
|---------|---------|
| `inlineCompletionEnabled` | Master on/off |
| `completionModel` | Model ID |
| `completionDebounceMs` | Typing debounce |
| `completionMaxTokens` | Max output tokens |
| `completionContextLines` | Surrounding lines in request |
| `completionRepositoryContextEnabled` | Indexer snippets |
| `completionTriggerOnTyping` | Automatic vs manual only |
| `completionMaxRequestsPerMinute` | Rate limit |
| `completionTimeoutMs` | Request timeout |

Command palette: **AI: Enable/Disable/Trigger/Cancel Inline Completion**, **AI: Open Inline Completion Settings**.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Space` | Trigger completion |
| `Tab` | Accept (Monaco default) |
| `Esc` | Reject / cancel |

**Not implemented:** `Ctrl+Right` partial word acceptance.

## Verification

```bash
# Start AI API (port 8000)
cd services/ai-api
uvicorn ai_api.main:app --port 8000

# Run E2E (builds desktop, launches Electron + Playwright)
cd apps/desktop
npm run verify:completion
```

E2E coverage includes: workspace open/file open, automatic completion, ghost text, Tab accept, Esc reject, Ctrl+Space, rapid typing cancellation, stale protection, cursor movement, tab switching, workspace switching, workspace close cleanup, unsaved buffer content, sensitive file protection, AI offline/recovery, settings UI, command palette, repository context (with indexer on :8002), post-accept cooldown, and lightweight Phase 13 regression (explorer, terminal, git).

Unit tests: `apps/desktop/tests/completionController.test.ts`, `completionStore.test.ts`, `completionContext.test.ts`.

## Evaluation

Benchmark: `completion-mini` with metrics `exact_match`, `normalized_match`, `prefix_preservation`, `suffix_preservation`, `syntax_validity`, `latency_ms`.

## Known Limitations

- Development mock uses deterministic prefix rules (`const user = await db.` → `findById(id);`), not real model quality
- Repository context requires indexer on `http://127.0.0.1:8002`; failures are graceful (local completion still works)
- No streaming completions endpoint
- No partial-word (`Ctrl+Right`) acceptance
- Agent service (`:8001`) is not required for completion; Phase 13 agent/chat streams are covered by pytest, not completion E2E
