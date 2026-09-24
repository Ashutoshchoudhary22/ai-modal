# Browser Agent — Phase 9

Secure, bounded browser automation integrated with the Phase 6 agent loop and Phase 5 tool registry.

## Architecture

```
User Task
   ↓
BrowserAgentOrchestrator
   ↓
LoopAgentRunner + StructuredModelClient
   ↓
browser.* tools (ToolRegistry)
   ↓
BrowserProvider
   ├── DevelopmentMockBrowserProvider (tests/dev)
   └── LocalPlaywrightBrowserProvider (optional)
          ↓
       Browser Session → Observation → Actions
```

**Security boundary:** Model decisions pass through schema validation, `browser_agent` policy, and URL/domain/SSRF policy before execution. Web page content is untrusted data.

## BrowserProvider

Protocol in `services/agent/src/agent/browser/providers/base.py`:

- `create_session()` — isolated session per run
- Session methods: `navigate`, `observe`, `click`, `fill`, `type_text`, `select`, `press`, `scroll`, `wait`, `screenshot`, `back`, `forward`, `reload`, `close`

Factory: `create_browser_provider()` reads `AI_PLATFORM_BROWSER_PROVIDER`.

| Provider | Value | Notes |
|----------|-------|-------|
| Mock | `development_mock` | Deterministic fixtures, default for tests |
| Playwright | `playwright` | Optional; returns `BROWSER_PROVIDER_UNAVAILABLE` if not configured |

## Sessions

`BrowserSession` (protocol) tracks safe metadata only: URL, title, action/navigation counts, observation ID. No cookies, tokens, or credentials.

Sessions are keyed by `request_id` in `BrowserSessionRegistry` and cleaned up in `finally` after each run.

## Observations

Bounded `BrowserObservation` with:

- `observation_id` (e.g. `obs_3`)
- Structured `elements` with temporary `element_id` (e1, e2, …)
- Accessibility summary
- Optional `screenshot_reference`
- Sensitive field masking (`[REDACTED]`)

Stale element references return `STALE_ELEMENT_REFERENCE` when `observation_id` does not match the current page state.

## Browser Tools

Registered in `ToolRegistry` with `ToolPermission.BROWSER`:

- `browser.navigate`, `browser.observe`, `browser.click`, `browser.fill`, `browser.type`
- `browser.select`, `browser.scroll`, `browser.press`, `browser.wait`
- `browser.screenshot`, `browser.back`, `browser.forward`, `browser.reload`

No `browser.evaluate_javascript` or `browser.http_request`.

## Policy

`browser_agent` policy (`services/agent/src/agent/loop/policy.py`):

- Browser tools only — denies `terminal.exec`, `file.write`, `git.*`
- `ToolPermission.BROWSER` required

URL policy (`services/agent/src/agent/browser/policy.py`):

- Allows `http`/`https` only
- Blocks `file:`, `javascript:`, `data:`, metadata endpoints, private IPs
- Configurable allowlist/blocklist
- Localhost allowed when `AI_PLATFORM_BROWSER_ALLOW_LOCALHOST=true`

## API

| Endpoint | Description |
|----------|-------------|
| `POST /v1/browser/runs` | Start browser agent run |
| `GET /v1/browser/runs/{run_id}` | Run status |
| `POST /v1/browser/runs/{run_id}/cancel` | Cancel run |
| `POST /v1/browser/runs/stream` | SSE stream |

## Configuration

See `.env.example` — `AI_PLATFORM_BROWSER_*` settings for provider, timeouts, limits, domains.

## Testing

- Unit tests use `DevelopmentMockBrowserProvider` and fixtures in `services/agent/tests/fixtures/browser/`
- No network or browser binaries required for standard test suite
- Playwright smoke test optional when Playwright is installed

## Database

No new migration required. Browser run metadata uses existing agent run infrastructure (`agent_runs` / `agent_run_events`).

## Phase 10 Boundary

**Implemented:** Task → session → observe → model decision → browser action → validate → bounded retry → final result.

**Deferred:** Multimodal vision+language model architecture, unrestricted web research, CAPTCHA solving, credential harvesting, stealth automation.
