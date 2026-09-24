"""SFT training entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from training.core.errors import (
    TrainingConfigError,
    TrainingDependencyError,
    TrainingRegistryError,
)
from training.core.trainer import run_training


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Supervised fine-tuning for coding models")
    parser.add_argument("--config", required=True, help="Path to YAML training config")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config).resolve()
    try:
        final_dir = run_training(config_path)
    except TrainingDependencyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (TrainingConfigError, TrainingRegistryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: training failed: {exc}", file=sys.stderr)
        raise

    print(f"Training complete. Final model saved to: {final_dir}")
    if "smoke" in config_path.name.lower():
        print("SMOKE TEST ONLY — not a production coding model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
