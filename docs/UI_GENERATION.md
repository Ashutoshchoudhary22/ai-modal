# UI Generation (Phase 7)

Phase 7 generates UI from natural-language requirements using repository-aware coding tools and the Phase 6 Agent Loop. Screenshot understanding and visual screenshot-to-code are intentionally deferred to **Phase 8**.

## Architecture

```text
POST /v1/ui/generate
        │
        ▼
   UIGenerator
        │
        ├── Framework detection
        ├── UI repository context
        ├── UISpec + ImplementationPlan
        │
        ▼
   LoopAgentRunner (Phase 6)
        │
        ▼
   ToolRegistry (Phase 5)
        │
        ▼
   Workspace files + validation
```

## Supported frameworks

Detected from `package.json` and project structure:

| Framework | Detection |
|-----------|-----------|
| Next.js App Router | `next` + `app/` directory |
| Next.js Pages Router | `next` + `pages/` |
| React + Vite | `vite` + `react` |
| React | `react` dependency |

Styling: Tailwind, CSS Modules, plain CSS, SCSS, styled-components.

## API

### Generate UI

```http
POST /v1/ui/generate
{
  "workspace_id": "my-ws",
  "prompt": "Create a responsive login page",
  "target": "page",
  "route": "/login",
  "responsive": true,
  "accessibility": true,
  "validation_mode": "build",
  "root_path": "/path/to/frontend"
}
```

### Inspect UI run

```http
GET /v1/ui/runs/{run_id}
```

### Stream (SSE)

```http
POST /v1/ui/generate/stream
```

## Policies

| Policy | Mode | Behavior |
|--------|------|----------|
| `ui_generation` | Write + execute | Creates/modifies UI files |
| `ui_read_only` | Analysis target | Read/search only |

## Validation modes

`none`, `diagnostics`, `build`, `test`, `full`

Commands are read from `package.json` scripts. Dependencies are **not** auto-installed.

## Configuration

| Variable | Default |
|----------|---------|
| `AI_PLATFORM_UI_GENERATION_ENABLED` | `true` |
| `AI_PLATFORM_UI_MAX_CONTEXT_CHARS` | `24000` |
| `AI_PLATFORM_UI_MAX_FILES` | `40` |
| `AI_PLATFORM_UI_MAX_COMPONENTS` | `30` |
| `AI_PLATFORM_UI_DEFAULT_VALIDATION` | `build` |
| `AI_PLATFORM_UI_MAX_GENERATION_FILES` | `20` |

## Component reuse

Before creating components, the planner searches existing `Button`, `Input`, `Card`, etc. via repository context and symbol index.

## Security

- Workspace sandbox (Phase 5)
- Sensitive file protection
- Terminal policy (no `npm install` by default)
- Prompt injection: repository content is untrusted data
- Git remains read-only

## Known limitations

1. No screenshot-to-code (Phase 8)
2. No browser automation (Phase 9)
3. No automatic dependency installation
4. No visual correctness validation
5. No autonomous deployment

## Phase boundary

> Phase 7 generates UI from natural-language requirements using repository-aware coding tools. Screenshot understanding belongs to Phase 8.
