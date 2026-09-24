"""SFT training entry point — Phase 2 implementation."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Supervised fine-tuning for coding models")
    parser.add_argument("--config", required=True, help="Path to YAML training config")
    args = parser.parse_args()
    print(f"Training pipeline not yet implemented. Config: {args.config}")
    print("See ROADMAP.md Phase 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
