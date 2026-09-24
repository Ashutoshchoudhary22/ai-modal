# Database Schema

MySQL 8.0+ — multi-tenant SaaS design.

Schema version: `001_initial`  
Init script: `infra/docker/mysql/init.sql`

---

## Entity Relationship Overview

```
organizations ──┬── teams ──┬── workspaces ──┬── projects
                │           │                │
                │           │                └── agent_sessions
                │           │
                │           └── workspace_members
                │
                ├── users (via organization_members)
                ├── api_keys
                ├── subscriptions
                └── usage_records

models ── model_versions ── benchmark_runs
datasets ── dataset_versions ── dataset_entries (metadata only; blobs external)

audit_logs (append-only)
```

---

## Core Tables

### `organizations`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| name | VARCHAR(255) | |
| slug | VARCHAR(100) UNIQUE | URL-safe |
| plan | VARCHAR(50) | free, pro, enterprise |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| email | VARCHAR(255) UNIQUE | |
| password_hash | VARCHAR(255) | nullable if SSO |
| display_name | VARCHAR(255) | |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMP | |

### `organization_members`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| organization_id | CHAR(36) FK → organizations | |
| user_id | CHAR(36) FK → users | |
| role | VARCHAR(50) | owner, admin, member |
| UNIQUE(organization_id, user_id) | | |

### `teams`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| organization_id | CHAR(36) FK | |
| name | VARCHAR(255) | |

### `workspaces`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| team_id | CHAR(36) FK → teams | |
| name | VARCHAR(255) | |
| root_path | TEXT | server-side path or remote URI |
| settings | JSON | sandbox, allowed commands |
| created_at | TIMESTAMP | |

### `projects`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| workspace_id | CHAR(36) FK | |
| name | VARCHAR(255) | |
| description | TEXT | |
| metadata | JSON | language, framework hints |

---

## Agent & Sessions

### `agent_sessions`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| project_id | CHAR(36) FK | nullable |
| workspace_id | CHAR(36) FK | |
| user_id | CHAR(36) FK | |
| task | TEXT | original user request |
| status | VARCHAR(50) | created, running, completed, failed, cancelled |
| model_id | VARCHAR(100) | |
| max_iterations | INT | |
| iteration_count | INT | default 0 |
| summary | TEXT | final summary |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

### `agent_events`

Append-only event log (mirrors WebSocket stream).

| Column | Type | Notes |
|--------|------|-------|
| id | BIGINT AUTO_INCREMENT PK | |
| session_id | CHAR(36) FK | |
| event_type | VARCHAR(50) | plan, tool_call, tool_result, message, error |
| payload | JSON | |
| created_at | TIMESTAMP | |

Index: `(session_id, created_at)`.

---

## Code Indexing

### `code_indices`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| workspace_id | CHAR(36) FK UNIQUE | one active index per workspace |
| status | VARCHAR(50) | indexing, ready, failed |
| file_count | INT | |
| symbol_count | INT | |
| index_hash | VARCHAR(64) | content hash |
| indexed_at | TIMESTAMP | |

### `indexed_files`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGINT AUTO_INCREMENT PK | |
| index_id | CHAR(36) FK | |
| path | TEXT | relative path |
| language | VARCHAR(50) | |
| content_hash | VARCHAR(64) | |
| size_bytes | INT | |

Vector embeddings stored in external vector DB (e.g. Qdrant or dedicated search service); reference via `embedding_id` in future migration.

---

## Models & Training

### `models`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| name | VARCHAR(100) | e.g. code-assistant |
| modality | VARCHAR(50) | text, multimodal |
| description | TEXT | |

### `model_versions`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| model_id | CHAR(36) FK | |
| version | VARCHAR(50) | semver |
| provider | VARCHAR(50) | development_mock, local_hf, proprietary |
| artifact_uri | TEXT | S3/path to weights |
| config_hash | VARCHAR(64) | training config fingerprint |
| dataset_version_id | CHAR(36) FK | nullable |
| is_active | BOOLEAN | deployment flag |
| created_at | TIMESTAMP | |

### `datasets`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| name | VARCHAR(100) | |
| category | VARCHAR(50) | code_completion, bug_fix, ui_gen, ... |
| license | VARCHAR(100) | SPDX |
| description | TEXT | |

### `dataset_versions`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| dataset_id | CHAR(36) FK | |
| version | VARCHAR(50) | |
| manifest_uri | TEXT | |
| entry_count | INT | |
| content_hash | VARCHAR(64) | |
| created_at | TIMESTAMP | |

### `dataset_sources` (Phase 3)

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | |
| dataset_id | CHAR(36) FK | |
| source_name | VARCHAR(255) | |
| source_type | VARCHAR(50) | internal, synthetic, external, ... |
| source_reference | TEXT | nullable URL/path |
| license | VARCHAR(100) | |
| created_at | TIMESTAMP | |

### `dataset_processing_runs` (Phase 3)

Tracks each dataset processing execution. Large JSONL bodies remain on filesystem.

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | |
| dataset_version_id | CHAR(36) FK | |
| status | VARCHAR(50) | completed, failed, ... |
| input_records | INT | |
| valid_records | INT | |
| invalid_records | INT | |
| exact_duplicates | INT | |
| normalized_duplicates | INT | |
| filtered_records | INT | |
| output_records | INT | |
| train_records | INT | |
| validation_records | INT | |
| test_records | INT | |
| raw_hash | VARCHAR(64) | |
| normalized_hash | VARCHAR(64) | |
| processed_hash | VARCHAR(64) | |
| processing_config_hash | VARCHAR(64) | |
| report_uri | TEXT | quality_report.json path |
| processed_uri | TEXT | processed artifact directory |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | nullable |

### `training_jobs`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| job_type | VARCHAR(50) | sft, dpo, eval |
| config_path | TEXT | |
| dataset_version_id | CHAR(36) FK | |
| status | VARCHAR(50) | queued, running, completed, failed |
| output_model_version_id | CHAR(36) FK | nullable |
| metrics | JSON | |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

### `benchmark_runs`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| model_version_id | CHAR(36) FK | |
| benchmark_name | VARCHAR(100) | |
| dataset_version_id | CHAR(36) FK | |
| config | JSON | |
| results | JSON | scores, per-task breakdown |
| run_at | TIMESTAMP | |

---

## Auth & Billing

### `api_keys`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| organization_id | CHAR(36) FK | |
| name | VARCHAR(255) | |
| key_prefix | VARCHAR(12) | display only |
| key_hash | VARCHAR(255) | bcrypt/sha256 |
| scopes | JSON | |
| expires_at | TIMESTAMP | nullable |
| revoked_at | TIMESTAMP | nullable |
| created_at | TIMESTAMP | |

### `usage_records`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGINT AUTO_INCREMENT PK | |
| organization_id | CHAR(36) FK | |
| user_id | CHAR(36) FK | nullable |
| session_id | CHAR(36) FK | nullable |
| model_id | VARCHAR(100) | |
| prompt_tokens | INT | |
| completion_tokens | INT | |
| tool_calls | INT | default 0 |
| recorded_at | TIMESTAMP | |

Partition by month in production.

### `subscriptions`

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| organization_id | CHAR(36) FK UNIQUE | |
| plan | VARCHAR(50) | |
| status | VARCHAR(50) | active, cancelled, past_due |
| external_id | VARCHAR(255) | Stripe/etc |
| current_period_start | TIMESTAMP | |
| current_period_end | TIMESTAMP | |

---

## Audit

### `audit_logs`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGINT AUTO_INCREMENT PK | |
| organization_id | CHAR(36) FK | |
| user_id | CHAR(36) FK | nullable |
| action | VARCHAR(100) | agent.tool_call, auth.login, ... |
| resource_type | VARCHAR(50) | |
| resource_id | VARCHAR(255) | |
| metadata | JSON | |
| ip_address | VARCHAR(45) | nullable, IPv4/IPv6 |
| created_at | TIMESTAMP | |

Retention: configurable; default 365 days.

---

## Model Registry (Phase 1 — IMPLEMENTED)

### `provider_model_registry`

Runtime registry of available model providers and model IDs. Used by the AI API `/v1/models` endpoint when MySQL is available.

| Column | Type | Notes |
|--------|------|-------|
| id | CHAR(36) PK | UUID string |
| model_id | VARCHAR(100) UNIQUE | e.g. `development-mock-v1` |
| model_name | VARCHAR(255) | Display name |
| version | VARCHAR(50) | Semantic version |
| provider | VARCHAR(50) | `development_mock`, `local`, `proprietary` |
| architecture | VARCHAR(100) | nullable |
| capabilities | JSON | e.g. generate, stream, embed |
| context_length | INT | nullable |
| modalities | JSON | e.g. `["text"]` |
| status | VARCHAR(50) | `registered`, `active`, ... |
| local_path | TEXT | nullable local checkpoint path |
| created_at | TIMESTAMP | |

Migration: `infra/docker/mysql/migrations/002_provider_model_registry.sql`

**Note:** Embeddings and model checkpoints are **not** stored in MySQL. Vector embeddings use the pluggable `VectorStore` abstraction (in-memory/filesystem for dev).

### repository_files (Phase 4)

| Column | Type | Description |
|--------|------|-------------|
| id | CHAR(64) PK | Deterministic file id (`workspace_id:relative_path`) |
| workspace_id | CHAR(36) FK | → `workspaces(id)` |
| relative_path | VARCHAR(2048) | Normalized POSIX-style path |
| language | VARCHAR(50) | Detected language |
| size_bytes | BIGINT | File size |
| sha256 | CHAR(64) | Content hash for incremental indexing |
| line_count | INT | Line count |
| is_binary | TINYINT | Binary flag |
| is_generated | TINYINT | Generated flag |
| is_ignored | TINYINT | Ignored flag |
| parser_status | VARCHAR(50) | `ok`, `partial`, `error`, etc. |
| index_version | INT | Index version |
| parser_version | VARCHAR(50) | Parser version |
| first_indexed_at | TIMESTAMP | First index time |
| last_indexed_at | TIMESTAMP | Last index time |

Unique: `(workspace_id, relative_path)`

### repository_index_runs, repository_symbols, repository_imports

See migration `004_repository_intelligence.sql` and `005_repository_files.sql`. Symbols and imports include optional `file_id` FK-style references to `repository_files.id`.

---

## Indexes (Summary)

- `users(email)`
- `organization_members(organization_id, user_id)`
- `agent_sessions(workspace_id, status)`
- `agent_events(session_id, created_at)`
- `usage_records(organization_id, recorded_at)`
- `model_versions(model_id, is_active)`

---

## Migrations

- Bootstrap: `infra/docker/mysql/init.sql` (schema `001_initial`)
- Phase 1: `infra/docker/mysql/migrations/002_provider_model_registry.sql`
- Phase 3: `infra/docker/mysql/migrations/003_dataset_system.sql`
- Phase 4: `infra/docker/mysql/migrations/004_repository_intelligence.sql`
- Phase 4: `infra/docker/mysql/migrations/005_repository_files.sql`

Apply migrations:

```bash
make db-migrate    # bootstrap empty DB + apply pending migrations
make db-status     # show applied migrations
```

Tracked in `schema_migrations` table. Future: Alembic (Python) or sql-migrate for incremental changes.

---

*Last updated: Phase 4 — Repository Intelligence*
