# Agent Loop (Phase 6)

Phase 6 provides a **bounded, observable, policy-controlled agent loop** that orchestrates Phase 5 coding tools. It does **not** provide unrestricted autonomous execution.

## Architecture

```text
User Task
   │
   ▼
POST /v1/agent/runs
   │
   ▼
LoopAgentRunner
   ├── AgentState
   ├── AgentPolicy (read_only | coding | testing)
   ├── AgentLimits
   ├── AgentModelClient → ModelProvider
   ├── ToolCallValidator
   ├── ToolExecutor → ToolRegistry
   └── EventSink
```

## Run states

`queued` → `running` → (`waiting_for_tool` → `processing_result`)* → `completed` | `failed` | `cancelled` | `limit_reached`

## Model decisions

The model returns structured JSON:

```json
{"type": "final", "message": "Task complete."}
```

or

```json
{"type": "tool_call", "tool_name": "file.read", "arguments": {"path": "src/app.py"}}
```

Tool schemas are injected dynamically from the Tool Registry.

## Policies

| Policy | Write | Execute | Tools |
|--------|-------|---------|-------|
| `read_only` | No | No | read/search/git read |
| `coding` | Yes | Yes | all Phase 5 tools |
| `testing` | Yes | Yes | coding + diagnostics validation |

Git remains read-only in all policies.

## Limits (configurable)

- `AI_PLATFORM_AGENT_MAX_ITERATIONS` (default 25)
- `AI_PLATFORM_AGENT_MAX_TOOL_CALLS` (50)
- `AI_PLATFORM_AGENT_MAX_SAME_TOOL_CALLS` (10)
- `AI_PLATFORM_AGENT_MAX_MODEL_CALLS` (30)
- `AI_PLATFORM_AGENT_MAX_RUNTIME` (600s)
- `AI_PLATFORM_AGENT_MAX_CONTEXT_CHARS` (32000)
- `AI_PLATFORM_AGENT_MAX_TOOL_RESULT_CHARS` (8000)
- `AI_PLATFORM_AGENT_MAX_RETRIES` (3)

## API

### Start run

```http
POST /v1/agent/runs
{
  "workspace_id": "my-ws",
  "task": "Fix the login validation bug",
  "policy": "coding",
  "root_path": "/path/to/workspace"
}
```

### Inspect run

```http
GET /v1/agent/runs/{run_id}
```

### Stream events (SSE)

```http
POST /v1/agent/runs/stream
```

Event types: `run.started`, `model.started`, `model.completed`, `tool.started`, `tool.completed`, `tool.failed`, `observation.created`, `run.completed`, `run.failed`, `run.cancelled`, `run.limit_reached`

### Cancel

```http
POST /v1/agent/runs/{run_id}/cancel
```

## Security

- All tool calls go through `ToolRegistry.execute()` with Phase 5 security
- Tool outputs are treated as **untrusted data** (prompt injection resistance)
- Sensitive files, path traversal, and terminal policy remain enforced
- No silent fallback to development mock in production paths

## Persistence

- Run metadata: in-memory store (default) + MySQL migration `006_agent_runs.sql`
- Large prompts/tool outputs are **not** stored in MySQL by default
- Event metadata can be stored in `agent_run_events` (bounded fields only)

## Testing

Tests use `ScriptedModelClient` for deterministic orchestration without a live LLM.

## Known limitations

1. Tool calls are processed **sequentially** (no parallel execution)
2. Cancellation is cooperative — in-flight OS processes may not stop immediately
3. Streaming delivers events after run segments complete (batch SSE)
4. No long-term cross-session agent memory
5. No autonomous Git commits/push

## Phase boundary

> Phase 6 provides a bounded Agent Loop. UI generation is implemented in **Phase 7** — see [UI_GENERATION.md](./UI_GENERATION.md).
