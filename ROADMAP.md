# AI Platform — Delivery Roadmap

Phased implementation plan. Each phase must pass tests and documentation updates before the next begins.

**Legend:** ✅ Complete · 🔄 In Progress · ⬜ Planned

---

## Phase 0 — Project Foundation ✅

**Goal:** Architecture, monorepo scaffold, dev environment, CI baseline.

| Deliverable | Status |
|-------------|--------|
| ARCHITECTURE.md | ✅ |
| ROADMAP.md | ✅ |
| DEVELOPMENT_RULES.md | ✅ |
| PROJECT_STRUCTURE.md | ✅ |
| README.md | ✅ |
| API specification (`docs/API.md`) | ✅ |
| Database schema (`docs/DATABASE_SCHEMA.md`) | ✅ |
| Environment config (`docs/ENVIRONMENT.md`, `.env.example`) | ✅ |
| Docker Compose dev stack | ✅ |
| Python + Node tooling, lint, tests | ✅ |
| Initial CI workflow | ✅ |

**Exit criteria:** `make test` / `npm test` / `pytest` pass; Docker services start; docs reviewed.

---

## Phase 1 — Model Abstraction ✅

**Goal:** Replaceable `ModelProvider` with mock and local implementations.

| Deliverable | Status |
|-------------|--------|
| `ModelProvider` protocol in `packages/protocol` | ✅ |
| `DevelopmentMockProvider` | ✅ |
| `LocalModelProvider` (HF Transformers) | ✅ |
| `ProprietaryModelProvider` placeholder | ✅ |
| Model registry (MySQL) | ✅ |
| Provider factory | ✅ |
| AI API integration (`/ready`, `/v1/chat`, streaming) | ✅ |
| Unit + integration tests | ✅ |
| Documentation (`docs/MODEL_PROVIDER.md`, `docs/LOCAL_MODEL_SETUP.md`) | ✅ |
| Future-compatible agent/tool/indexer protocol stubs | ✅ |

**Exit criteria:** Services call providers only through interface; no hard-coded model logic in agents. ✅

---

## Phase 2 — Coding Model Pipeline ✅

**Goal:** Configurable SFT training for code models.

| Deliverable | Status |
|-------------|--------|
| Tokenizer management | ✅ |
| Dataset loading + validation | ✅ |
| Cleaning, dedup, language detection | ✅ (language metadata; detection PLANNED Phase 3) |
| Train/val/test split | ✅ |
| `training/sft/train.py --config` | ✅ |
| LoRA/QLoRA + full FT configs | ✅ |
| Auto CUDA device detection | ✅ |
| Checkpoint + experiment tracking | ✅ |

**Exit criteria:** Training runs on mock/small dataset; checkpoints saved; config documented. ✅

See [docs/TRAINING.md](./docs/TRAINING.md).

---

## Phase 3 — Dataset System ✅

**Goal:** Versioned, governed dataset pipeline.

| Deliverable | Status |
|-------------|--------|
| Dataset manifest format | ✅ |
| Provenance, hashing, dedup | ✅ |
| License + quality metadata | ✅ |
| Instruction / conversation / completion / preference schemas | ✅ |
| Validation + processing CLI | ✅ |
| MySQL dataset metadata | ✅ |
| Quality reports + leakage checks | ✅ |

**Exit criteria:** Sample datasets validate; train/test separation enforced. ✅

See [docs/DATASETS.md](./docs/DATASETS.md).

---

## Phase 4 — Repository Intelligence ✅

**Goal:** Index and retrieve relevant code context.

| Deliverable | Status |
|-------------|--------|
| Workspace scanner | ✅ |
| Tree-sitter multi-language parsing | ✅ |
| Symbol + import graph | ✅ |
| MySQL persistence (files, symbols, imports, runs) | ✅ |
| Workspace creation API | ✅ |
| Git read-only metadata | ✅ |
| Embeddings + vector index abstraction | ✅ |
| Semantic + lexical search API | ✅ |

**Exit criteria:** "Fix auth bug" retrieves auth-related files in test repo. ✅

See [docs/REPOSITORY_INTELLIGENCE.md](./docs/REPOSITORY_INTELLIGENCE.md).

---

## Phase 5 — Coding Agent Tools ✅

**Goal:** Deterministic, sandboxed tool library with schemas, permissions, and API.

| Deliverable | Status |
|-------------|--------|
| Tool abstraction + registry | ✅ |
| File tools (read/list/write/edit) | ✅ |
| Code tools (search/symbols/context) | ✅ |
| Terminal tool + command policy + executor abstraction | ✅ |
| Git read-only tools (status/diff) | ✅ |
| Diagnostics tool (configurable) | ✅ |
| Permission model + workspace security | ✅ |
| Tool API (`GET /v1/tools`, `POST /v1/tools/execute`) | ✅ |
| Unit, security, integration tests | ✅ |
| In-memory audit logging | ✅ |

**Exit criteria:** Each tool has unit tests; dangerous ops blocked by policy; no unrestricted terminal. ✅

See [docs/CODING_AGENT_TOOLS.md](./docs/CODING_AGENT_TOOLS.md).

> Phase 5 does **not** include the Agent Loop (Phase 6).

---

## Phase 6 — Agent Loop ✅

**Goal:** Bounded model → tool → observe loop with policies, limits, and streaming events.

| Deliverable | Status |
|-------------|--------|
| AgentRunner + AgentState | ✅ |
| ModelProvider integration (structured decisions) | ✅ |
| Tool call validation + policy enforcement | ✅ |
| Iteration/tool/runtime limits + cancellation | ✅ |
| Read-only and coding policies | ✅ |
| Agent events + SSE streaming API | ✅ |
| Agent API (`POST/GET /v1/agent/runs`, stream, cancel) | ✅ |
| In-memory run store + MySQL migration | ✅ |
| Deterministic scripted model tests | ✅ |
| Security + prompt-injection tests | ✅ |

**Exit criteria:** End-to-end fixture workflow completes within iteration cap; limits enforced. ✅

See [docs/AGENT_LOOP.md](./docs/AGENT_LOOP.md).

---

## Phase 7 — UI Generation ✅

**Goal:** Repository-aware UI generation via Agent Loop.

| Deliverable | Status |
|-------------|--------|
| Framework detection (Next.js, Vite React) | ✅ |
| UISpec / PageSpec / ComponentSpec | ✅ |
| UI planner + component reuse | ✅ |
| UIGenerator + Agent Loop integration | ✅ |
| Validation (diagnostics/build/test) | ✅ |
| API (`POST /v1/ui/generate`, stream, GET run) | ✅ |
| Security + prompt injection tests | ✅ |

**Exit criteria:** NL UI request → framework-aware code in workspace with bounded validation. ✅

See [docs/UI_GENERATION.md](./docs/UI_GENERATION.md).

---

## Phase 8 — Screenshot-to-Code ✅

**Goal:** Vision → layout → code generation with visual validation.

| Deliverable | Status |
|-------------|--------|
| VisionProvider abstraction | ✅ |
| Image validation (PNG/JPEG/WebP) | ✅ |
| VisualAnalysis → UISpec | ✅ |
| Phase 7 planner/generator integration | ✅ |
| UIRenderer + VisualComparator | ✅ |
| Bounded visual fix loop | ✅ |
| API (`POST /v1/ui/screenshot-to-code`, stream, GET run) | ✅ |
| Security + prompt-injection tests | ✅ |

**Exit criteria:** Screenshot → vision analysis → UI code → visual comparison with bounded correction. ✅

See [docs/SCREENSHOT_TO_CODE.md](./docs/SCREENSHOT_TO_CODE.md).

---

## Phase 9 — Browser Agent ✅

**Goal:** Secure, bounded browser agent for controlled web application testing.

| Deliverable | Status |
|-------------|--------|
| BrowserProvider abstraction (mock + Playwright stub) | ✅ |
| Browser sessions, observations, element IDs | ✅ |
| browser.* tools in ToolRegistry | ✅ |
| `browser_agent` policy (no shell/file/git) | ✅ |
| URL/domain/SSRF policy | ✅ |
| LoopAgentRunner integration | ✅ |
| API (`POST /v1/browser/runs`, stream, cancel, GET) | ✅ |
| Security + prompt-injection tests | ✅ |

**Exit criteria:** Task → observe → action → bounded retry → result with domain/SSRF enforcement. ✅

See [docs/BROWSER_AGENT.md](./docs/BROWSER_AGENT.md).

---

## Phase 10 — Multimodal Model Architecture ✅

**Goal:** Modular text + image inference architecture with provider independence.

| Deliverable | Status |
|-------------|--------|
| Multimodal protocol (`MultimodalRequest`, content types) | ✅ |
| `ImageProcessor`, `VisionEncoder`, `MultimodalProjector`, `MultimodalFusion` | ✅ |
| `MultimodalModel` + mock/local/proprietary providers | ✅ |
| Context/token accounting | ✅ |
| API (`POST /v1/multimodal/generate`, stream) | ✅ |
| Phase 8 `MultimodalVisionProvider` adapter | ✅ |
| Phase 9 browser observation adapter | ✅ |
| Security + deterministic tests | ✅ |

**Exit criteria:** Text + image → modular mock pipeline → structured/streaming output. ✅

See [docs/MULTIMODAL.md](./docs/MULTIMODAL.md).

---

## Phase 11 — Multimodal Training Strategy ✅

**Goal:** Reproducible multimodal SFT infrastructure with CPU smoke training.

| Deliverable | Status |
|-------------|--------|
| Multimodal JSONL dataset contract | ✅ |
| Dataset validation / fingerprint / leakage | ✅ |
| Preprocessing + collator + label masking | ✅ |
| Tiny trainable development model | ✅ |
| SFT + LoRA + checkpoint/resume | ✅ |
| CLI + minimal training API | ✅ |
| CPU smoke training (`multimodal-mini`) | ✅ |

See [docs/MULTIMODAL_TRAINING.md](./docs/MULTIMODAL_TRAINING.md).

---

## Phase 12 — Evaluation Framework ✅

**Goal:** Reproducible benchmarks tied to model versions and checkpoints.

| Deliverable | Status |
|-------------|--------|
| Benchmark + metric registries | ✅ |
| Coding sandbox evaluation | ✅ |
| Multimodal / screenshot / UI evaluation | ✅ |
| Agent + browser benchmarks | ✅ |
| Regression + comparison reports | ✅ |
| CLI + minimal API | ✅ |

See [docs/EVALUATION.md](./docs/EVALUATION.md).

---

## Phase 13 — Desktop IDE ✅

**Goal:** Electron app with Monaco, chat, terminal, agent, evaluation.

| Deliverable | Status |
|-------------|--------|
| Electron shell + secure preload | ✅ |
| Layout (explorer/editor/chat/terminal) | ✅ |
| Git, problems, diff panels | ✅ |
| Agent mode integration | ✅ |
| UI generation + screenshot-to-code | ✅ |
| Evaluation panel | ✅ |
| Command palette + search | ✅ |

See [docs/DESKTOP_IDE.md](./docs/DESKTOP_IDE.md).

---

## Phase 14 — Inline Coding ✅

**Goal:** Low-latency inline code completion (Copilot-style ghost text).

| Deliverable | Status |
|-------------|--------|
| Completion protocol + API | ✅ |
| Monaco inline completion provider | ✅ |
| Debounce / cancel / stale protection | ✅ |
| Repository-aware bounded context | ✅ |
| completion-mini benchmark | ✅ |
| Settings + status indicator | ✅ |

See [docs/INLINE_COMPLETION.md](./docs/INLINE_COMPLETION.md).

---

## Phase 15 — Security Hardening ⬜

**Goal:** Production-grade sandbox and audit.

| Deliverable | Status |
|-------------|--------|
| Command allowlist | ⬜ |
| Secrets vault integration | ⬜ |
| Audit log persistence | ⬜ |

---

## Phase 16 — Multi-Tenant SaaS ⬜

**Goal:** Orgs, billing, API keys, usage.

| Deliverable | Status |
|-------------|--------|
| Auth service | ⬜ |
| Tenant isolation | ⬜ |
| Usage metering | ⬜ |

---

## Phase 17 — Model Router ⬜

**Goal:** Task-aware model selection.

| Deliverable | Status |
|-------------|--------|
| Router rules + config | ⬜ |
| Fallback chains | ⬜ |

---

## Phase 18 — Observability ⬜

**Goal:** Metrics, tracing, admin dashboards.

| Deliverable | Status |
|-------------|--------|
| Prometheus/OpenTelemetry | ⬜ |
| Admin UI charts | ⬜ |

---

## Phase 19 — Continuous Learning ⬜

**Goal:** Governed feedback → training pipeline.

| Deliverable | Status |
|-------------|--------|
| Feedback ingestion | ⬜ |
| Quality gate + eval before train | ⬜ |

---

## Phase 20 — Developer Experience ⬜

**Goal:** Full CI/CD, integration/e2e tests, docs parity.

| Deliverable | Status |
|-------------|--------|
| E2E test suite | ⬜ |
| Release automation | ⬜ |
| Contributor guide | ⬜ |

---

## Milestone Timeline (Indicative)

| Quarter | Focus |
|---------|-------|
| Q1 | Phases 0–3 (foundation, model abstraction, training, datasets) |
| Q2 | Phases 4–6 (repo intel, agent tools, agent loop) |
| Q3 | Phases 7–12 (UI, browser, multimodal, eval) |
| Q4 | Phases 13–20 (IDE, SaaS, observability, continuous learning) |

*Timelines adjust based on team size and GPU availability.*

---

## Current Status

**Active phase:** Phase 14 — Inline Coding ✅  
**Next phase:** Phase 15 — Security Hardening

---

*Last updated: Phase 14*
