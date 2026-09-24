# Evaluation & Benchmarking (Phase 12)

Phase 12 adds a reproducible evaluation framework for coding, multimodal, UI, agent, and browser benchmarks.

## Architecture

```text
Benchmark Registry → Evaluation Runner → Model Adapter → Evaluator → Metrics → Reports
```

## CLI

```bash
python -m training.evaluation.cli list-benchmarks
python -m training.evaluation.cli validate --benchmark coding-mini
python -m training.evaluation.cli run --benchmark coding-mini --provider development_mock --dry-run
python -m training.evaluation.cli run --config training/configs/evaluation/coding-mini.yaml
python -m training.evaluation.cli report --run training/output/evaluation/runs/<run_id>
python -m training.evaluation.cli compare --run-a <dir> --run-b <dir>
```

## Benchmarks

Development fixtures live under `data/benchmarks/`:

- `coding-mini`, `debugging-mini`
- `vision-mini`, `screenshot-analysis-mini`, `screenshot-to-code-mini`
- `agent-mini`, `browser-agent-mini`
- `security-prompt-injection-mini`

## Outputs

Each run writes:

```text
training/output/evaluation/runs/<run_id>/
  config.json
  summary.json
  metrics.json
  samples.jsonl
  reproducibility.json
  report.md
```

## Security

- Generated code executes only in isolated temporary workspaces with timeouts
- Browser benchmarks use local fixture policies only
- Reports redact secrets and avoid storing raw sensitive inputs

## Phase boundary

Phase 12 does not implement distributed evaluation, preference optimization, or continuous learning.
