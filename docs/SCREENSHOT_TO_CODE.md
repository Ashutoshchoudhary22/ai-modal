# Screenshot-to-Code (Phase 8)

Phase 8 converts screenshots into framework-aware UI code using vision analysis, Phase 7 UI generation, and Phase 6 Agent Loop orchestration. Autonomous browser agents belong to **Phase 9**.

## Architecture

```text
Screenshot upload
       │
       ▼
Image validation
       │
       ▼
VisionProvider
       │
       ▼
VisualAnalysis
       │
       ▼
UISpec (Phase 7)
       │
       ▼
UI Planner + Repository Context
       │
       ▼
UIGenerator / Agent Loop
       │
       ▼
Phase 5 Tools → workspace files
       │
       ▼
Validation (diagnostics/build/test)
       │
       ▼
UIRenderer → screenshot
       │
       ▼
VisualComparator
       │
       ▼
Bounded visual fix loop
```

## Vision providers

| Provider | Purpose |
|----------|---------|
| `development_mock` | Deterministic test/dev analysis from fixtures |
| `local` | Future local vision model (explicit config required) |
| `proprietary` | Future internal multimodal model placeholder |

## Supported image formats

PNG, JPEG/JPG, WebP — validated by MIME type, extension, and decoded content.

## API

### Generate from base64

```http
POST /v1/ui/screenshot-to-code
{
  "workspace_id": "my-ws",
  "image_base64": "...",
  "image_mime_type": "image/png",
  "prompt": "simple-card",
  "root_path": "/path/to/frontend",
  "validation_mode": "build",
  "visual_validation_enabled": true
}
```

### Upload

```http
POST /v1/ui/screenshot-to-code/upload
```

### Run status

```http
GET /v1/ui/screenshot-to-code/runs/{run_id}
```

### Stream (SSE)

```http
POST /v1/ui/screenshot-to-code/stream
```

## Configuration

| Variable | Default |
|----------|---------|
| `AI_PLATFORM_SCREENSHOT_TO_CODE_ENABLED` | `true` |
| `AI_PLATFORM_VISION_PROVIDER` | `development_mock` |
| `AI_PLATFORM_VISION_MAX_IMAGE_BYTES` | `10485760` |
| `AI_PLATFORM_UI_RENDERER` | `development_mock` |
| `AI_PLATFORM_VISUAL_VALIDATION_THRESHOLD` | `0.85` |
| `AI_PLATFORM_VISUAL_MAX_ITERATIONS` | `3` |

## Security

- Images are validated for size, dimensions, and format
- Screenshot text is untrusted — tool policy is authoritative
- No automatic dependency installation
- No Git write operations
- Workspace isolation enforced

## Limitations

- Single-screenshot responsive inference is approximate
- Mock vision uses fixture analysis JSON in tests
- Local browser renderer requires optional Playwright (not Phase 9 agent)
- Proprietary vision model not yet implemented

## Phase boundary

> Phase 8: screenshot → code + visual validation. Phase 9: autonomous browser agent.
