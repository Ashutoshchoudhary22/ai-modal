"""CLI entry point for multimodal training."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from training.multimodal.errors import MultimodalTrainingError
from training.multimodal.trainer import run_multimodal_training


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multimodal supervised fine-tuning")
    parser.add_argument("--config", required=True, help="Path to YAML training config")
    parser.add_argument("--dataset", help="Override dataset path")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--device", help="Override device")
    parser.add_argument("--seed", type=int, help="Override random seed")
    parser.add_argument("--resume-from-checkpoint", help="Resume from checkpoint directory")
    parser.add_argument("--dry-run", action="store_true", help="Validate without training")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config).resolve()
    resume = Path(args.resume_from_checkpoint).resolve() if args.resume_from_checkpoint else None

    if args.dataset or args.output_dir or args.device or args.seed is not None:
        import yaml

        from training.multimodal.config import MultimodalTrainingConfig

        config = MultimodalTrainingConfig.model_validate(
            yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        )
        if args.dataset:
            config.dataset.path = args.dataset
        if args.output_dir:
            config.output.dir = args.output_dir
        if args.device:
            config.hardware.device = args.device
        if args.seed is not None:
            config.experiment.seed = args.seed
        override_path = config_path.parent / f".{config_path.stem}.override.yaml"
        override_path.write_text(
            yaml.safe_dump(config.model_dump(mode="json")),
            encoding="utf-8",
        )
        config_path = override_path

    try:
        final_dir = run_multimodal_training(
            config_path,
            dry_run=args.dry_run,
            resume_from_checkpoint=resume,
        )
    except MultimodalTrainingError as exc:
        print(f"ERROR [{exc.code}]: {exc.message}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"Training complete. Final checkpoint: {final_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
