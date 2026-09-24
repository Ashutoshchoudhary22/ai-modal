"""Dataset system CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from training.datasets.fingerprint import fingerprint_raw_file
from training.datasets.ingest import process_dataset
from training.datasets.inspect import inspect_dataset
from training.datasets.manifest import load_manifest
from training.datasets.report import QualityReport
from training.datasets.validation import validate_manifest_and_dataset


def _build_tokenizer_counter(model_id: str | None):
    if not model_id:
        return None
    try:
        from training.core.tokenizer import TokenizerAdapter

        adapter = TokenizerAdapter(model_id=model_id, max_length=4096)

        def counter(record):
            return adapter.count_tokens(record.dedup_key)

        return counter
    except ImportError:
        print(
            "Tokenizer statistics skipped: training[train] dependencies not installed",
            file=sys.stderr,
        )
        return None


def cmd_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    if args.input:
        manifest.records.raw_path = args.input
    counter = _build_tokenizer_counter(args.tokenizer_model)
    report = validate_manifest_and_dataset(
        manifest,
        manifest_path,
        tokenizer_counter=counter,
    )
    print(report.summary())
    return 0 if report.passed else 1


def cmd_inspect(args: argparse.Namespace) -> int:
    counter = _build_tokenizer_counter(args.tokenizer_model)
    report = inspect_dataset(Path(args.input), tokenizer_counter=counter)
    print(report.summary())
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    path = Path(args.input)
    print(fingerprint_raw_file(path))
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    manifest_path = Path(args.config if args.config else args.manifest)
    manifest = load_manifest(manifest_path)
    if args.input:
        manifest.records.raw_path = args.input
    counter = _build_tokenizer_counter(args.tokenizer_model)
    result = process_dataset(
        manifest,
        manifest_path,
        processed_dir=Path(args.output) if args.output else None,
        tokenizer_counter=counter,
        max_tokens=args.max_tokens,
    )
    print(result.quality_report.summary())
    if args.json:
        print(json.dumps(json.loads(result.quality_report.to_json()), indent=2))
    return 0 if result.leakage_passed and not result.quality_report.errors else 1


def cmd_report(args: argparse.Namespace) -> int:
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Report not found: {report_path}", file=sys.stderr)
        return 1
    data = json.loads(report_path.read_text(encoding="utf-8"))
    report = QualityReport(**data)
    print(report.summary())
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    return cmd_process(args)


def cmd_split(args: argparse.Namespace) -> int:
    args.output = args.output or None
    return cmd_process(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Platform dataset system")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate manifest and JSONL dataset")
    validate.add_argument("--input", required=True)
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--tokenizer-model", default=None)
    validate.set_defaults(func=cmd_validate)

    inspect = sub.add_parser("inspect", help="Inspect dataset without dumping all records")
    inspect.add_argument("input")
    inspect.add_argument("--tokenizer-model", default=None)
    inspect.set_defaults(func=cmd_inspect)

    fingerprint = sub.add_parser("fingerprint", help="Compute raw SHA-256 fingerprint")
    fingerprint.add_argument("input")
    fingerprint.set_defaults(func=cmd_fingerprint)

    process = sub.add_parser("process", help="Run full dataset processing pipeline")
    process.add_argument("--config", "--manifest", dest="manifest", required=True)
    process.add_argument("--input", default=None)
    process.add_argument("--output", default=None)
    process.add_argument("--tokenizer-model", default=None)
    process.add_argument("--max-tokens", type=int, default=None)
    process.add_argument("--json", action="store_true")
    process.set_defaults(func=cmd_process)

    ingest = sub.add_parser("ingest", help="Ingest and process a dataset")
    ingest.add_argument("--manifest", required=True)
    ingest.add_argument("--input", default=None)
    ingest.add_argument("--output", default=None)
    ingest.add_argument("--tokenizer-model", default=None)
    ingest.add_argument("--max-tokens", type=int, default=None)
    ingest.set_defaults(func=cmd_ingest)

    split = sub.add_parser("split", help="Process and split a dataset")
    split.add_argument("--manifest", required=True)
    split.add_argument("--input", default=None)
    split.add_argument("--output", default=None)
    split.set_defaults(func=cmd_split)

    report = sub.add_parser("report", help="Display a quality report JSON file")
    report.add_argument("report")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
