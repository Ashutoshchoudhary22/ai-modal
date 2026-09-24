# Coding Agent Tools (Phase 5)

Phase 5 provides **deterministic coding tools** that a future Agent Loop (Phase 6) can call. It does **not** implement autonomous planning, retries, or multi-step agent behavior.

## Architecture

```text
AI Model (future Agent Loop)
        │
        ▼
  Tool Registry  ← GET /v1/tools, POST /v1/tools/execute
        │
   ┌────┼────┬────────┬─────────┐
   ▼    ▼    ▼        ▼         ▼
 File  Code Terminal  Git   Diagnostics
 Tools Tools  Tool   Tools     Tool
   │    │       │       │         │
   ▼    ▼       ▼       ▼         ▼
Workspace  Code Indexer  CommandExecutor (local; sandbox-ready)
```

**Service:** `services/agent/` (FastAPI, default port 8001)

**Shared types:** `packages/protocol/src/ai_platform_protocol/tools/`

## Tool abstraction

Each tool implements:

- `name`, `description`, `input_schema` (`parameters_schema`), `permissions`
- `async execute(arguments, context) -> ToolResult`

Execution context (`ToolExecutionContext`):

| Field | Purpose |
|-------|---------|
| `workspace_id` | Logical workspace identifier |
| `workspace_root` | Resolved filesystem root (sandbox boundary) |
| `request_id` | Correlation ID |
| `actor_id` | Optional user/actor |
| `permissions` | Granted capability set |
| `timeout_sec` | Operation timeout hint |

Results (`ToolResult`):

| Field | Purpose |
|-------|---------|
| `success` | Whether the tool completed successfully |
| `output` | JSON string summary (when applicable) |
| `error` | Human-readable error |
| `error_code` | Structured error code |
| `metadata` | Structured payload for callers |

## Registered tools

| Tool | Permission | Description |
|------|------------|-------------|
| `file.read` | read | Read text file (optional line range) |
| `file.list` | read | List files/directories |
| `file.write` | write | Create or replace file |
| `file.edit` | write | Deterministic `old_text` → `new_text` edit |
| `code.search` | read | Lexical/hybrid repository search (Phase 4) |
| `code.symbols` | read | Symbol lookup from index |
| `code.context` | read | Structured context builder |
| `terminal.exec` | execute | Policy-restricted command execution |
| `git.status` | git_read | Read-only Git status |
| `git.diff` | git_read | Read-only Git diff |
| `code.diagnostics` | execute | Configured diagnostic commands |

## Permissions

| Permission | Tools |
|------------|-------|
| `read` | file.read, file.list, code.* (search/symbols/context) |
| `write` | file.write, file.edit |
| `execute` | terminal.exec, code.diagnostics |
| `git_read` | git.status, git.diff |

The registry checks permissions before execution. Full multi-tenant RBAC is deferred to later phases.

## Security model

### Workspace sandbox

All filesystem paths are resolved through Phase 4 path security (`code_indexer.security.resolve_relative_path`). Traversal (`../`), absolute paths outside the workspace, and symlink escapes are rejected.

### Sensitive files

Access to `.env`, keys, credentials, and patterns in `SENSITIVE_PATTERNS` is blocked by default (read and write). `.env.example` is allowed for read.

### Terminal restrictions

- **Not a full OS sandbox.** Commands run locally via `LocalCommandExecutor` with policy checks only.
- No `shell=True`; commands are parsed with `shlex.split`.
- Shell metacharacters (`;`, `|`, `&&`, etc.) are rejected.
- Allowlist/denylist for executables plus dangerous-argument patterns.
- Timeout and stdout/stderr size limits apply.
- Working directory is always the workspace root.

Future deployments can swap `LocalCommandExecutor` for a container/VM sandbox without changing tool interfaces.

### Git tools

Read-only in Phase 5. No commit, push, checkout, or other mutating Git operations.

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_PLATFORM_TOOLS_ENABLED` | `true` | Master switch |
| `AI_PLATFORM_TOOL_MAX_FILE_SIZE` | `1048576` | Max bytes per file read/write |
| `AI_PLATFORM_TOOL_MAX_OUTPUT` | `32000` | Max characters returned |
| `AI_PLATFORM_TOOL_WRITE_ENABLED` | `true` | Allow file.write/file.edit |
| `AI_PLATFORM_TERMINAL_ENABLED` | `true` | Allow terminal.exec |
| `AI_PLATFORM_TERMINAL_TIMEOUT` | `120` | Command timeout (seconds) |
| `AI_PLATFORM_TERMINAL_MAX_OUTPUT` | `32000` | Max terminal output chars |
| `AI_PLATFORM_TERMINAL_ALLOWED_COMMANDS` | (list) | Executable allowlist |
| `AI_PLATFORM_TERMINAL_DENIED_COMMANDS` | (list) | Executable denylist |
| `AI_PLATFORM_DIAGNOSTICS_COMMANDS` | (list) | Diagnostics for code.diagnostics |

## API

### List tools

```http
GET /v1/tools
```

Returns tool names, descriptions, parameter JSON schemas, and permissions.

### Execute tool

```http
POST /v1/tools/execute
Content-Type: application/json

{
  "workspace_id": "my-workspace",
  "tool_name": "file.read",
  "arguments": {"path": "src/app.py"},
  "root_path": "/optional/local/path/for-dev"
}
```

`root_path` is a development fallback when workspace metadata is not in MySQL.

## Error codes

Structured errors include: `TOOL_NOT_FOUND`, `INVALID_ARGUMENTS`, `PERMISSION_DENIED`, `WORKSPACE_NOT_FOUND`, `PATH_OUTSIDE_WORKSPACE`, `FILE_NOT_FOUND`, `FILE_IS_BINARY`, `FILE_TOO_LARGE`, `EDIT_TARGET_NOT_FOUND`, `EDIT_TARGET_AMBIGUOUS`, `COMMAND_NOT_ALLOWED`, `COMMAND_TIMEOUT`, `COMMAND_FAILED`, `GIT_NOT_REPOSITORY`, `SENSITIVE_FILE`, `TOOL_EXECUTION_FAILED`.

## Audit logging

Tool executions are recorded in an in-memory audit log (`agent.audit`) with request ID, workspace, tool name, duration, and success/error. Large payloads and secrets are not stored. MySQL persistence can be added in a later phase if required.

## Examples

**Read a file:**

```json
{"path": "src/app.py", "start_line": 1, "end_line": 40}
```

**Search code:**

```json
{"query": "createConnection", "limit": 10, "search_mode": "lexical"}
```

**Edit file (deterministic):**

```json
{
  "path": "src/app.py",
  "old_text": "PORT = 3000",
  "new_text": "PORT = 4000",
  "replace_all": false
}
```

**Terminal (allowlisted):**

```json
{"command": "pytest -q"}
```

## Known limitations

1. Terminal execution uses process-level policy, not container/VM isolation.
2. Audit log is in-memory only (not persisted to MySQL).
3. No agent loop, streaming tool events, or autonomous retries (Phase 6).
4. Git write operations are intentionally unavailable.
5. Browser and network tools are not implemented.

## Phase boundary

> Phase 5 provides deterministic coding tools. Autonomous planning and multi-step execution belong to **Phase 6 — Agent Loop**.
