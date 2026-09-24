# Inline Code Completion (Phase 14)

Copilot-style inline code completion for the AI Platform Desktop IDE.

## Architecture

```
Monaco Editor
      ↓
InlineCompletionController
      ↓
CompletionContextCollector
      ↓
POST /v1/completions (AI API)
      ↓
CompletionService → ModelProvider
      ↓
CompletionValidator
      ↓
Monaco ghost text
```

## Request Lifecycle

1. User types or presses `Ctrl+Space`
2. Debounce (default 250ms)
3. Collect prefix/suffix and bounded context
4. POST to `/v1/completions`
5. Validate response (stale check, sanitization)
6. Display as Monaco inline suggestion
7. `Tab` to accept, `Esc` to reject

## Security

- Sensitive files (`.env`, `.pem`, `.key`) blocked
- Workspace path validation on server
- Secret redaction before external provider calls
- No full repository upload — bounded context only

## Configuration

See `.env.example` for `AI_PLATFORM_COMPLETION_*` variables.

Desktop settings: **AI → Inline Completion** (via settings store).

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Space` | Trigger completion |
| `Tab` | Accept (Monaco default) |
| `Esc` | Reject |

## Evaluation

Benchmark: `completion-mini` with metrics `exact_match`, `normalized_match`, `prefix_preservation`, `suffix_preservation`, `syntax_validity`, `latency_ms`.

## Limitations

- Partial word acceptance depends on Monaco inline suggest support
- Repository context is bounded and optional
- Streaming completion endpoint optional (non-streaming default for latency)
- Development mock uses deterministic prefix rules, not real model quality
