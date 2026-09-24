# Dataset System (Phase 3)

Versioned, reproducible dataset pipeline for coding-model training.

## Concepts

- **Manifest** — JSON description of dataset identity, source, quality rules, preprocessing, dedup, and split config
- **JSONL** — one record per line; streamed parsing (no full-file load)
- **Processing run** — deterministic validate → normalize → filter → dedup → split → fingerprint
- **Provenance** — raw hash, normalized hash, processed hash, and processing config hash

## Supported record types

| Type | Fields |
|------|--------|
| Instruction | `instruction`, `input`, `output` |
| Conversation | `messages[]` with `role` / `content` |
| Completion | `prompt`, `completion` |
| Preference | `prompt`, `chosen`, `rejected` (schema only; training in later phase) |

## CLI

```bash
python -m training.datasets validate --input data/examples/coding-mini.jsonl --manifest data/examples/coding-mini.manifest.json
python -m training.datasets inspect data/examples/coding-mini.jsonl
python -m training.datasets fingerprint data/examples/coding-mini.jsonl
python -m training.datasets process --manifest data/examples/coding-mini.manifest.json --input data/examples/coding-mini.jsonl
python -m training.datasets report path/to/quality_report.json
```

Backward-compatible validation entry point:

```bash
python -m training.datasets.validate --input ... --manifest ...
```

## Deduplication

- **Exact** — SHA-256 of canonical `dedup_key`
- **Normalized** — per-field whitespace collapse before hashing (fixes `print('x')` vs `print( 'x' )`)

## Storage

- Processed artifacts: `training/data/processed/<name>/<version>/`
- MySQL metadata: `datasets`, `dataset_versions`, `dataset_processing_runs`
- Large bodies remain on filesystem; MySQL stores metadata only

## Training integration

Training configs reference:

```yaml
dataset:
  manifest: training/data/manifests/smoke_sft.json
  dataset_id: coding-mini      # optional
  dataset_version: "1.0.0"     # optional
```

Checkpoint metadata includes `dataset_id`, `dataset_version`, `dataset_hash`, and `processing_config_hash`.

## Migrations

```bash
make db-migrate    # bootstrap empty DB + apply SQL migrations
make db-status     # show applied migrations
```

## Limitations

- Semantic leakage detection is not implemented (exact/normalized hash overlap only)
- Preference training is not implemented (ingestion/validation only)
- Language auto-detection is planned for a later phase
