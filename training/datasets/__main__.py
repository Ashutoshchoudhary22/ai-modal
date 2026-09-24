"""Dataset system CLI entry point."""

from __future__ import annotations

import sys

from training.datasets.cli import main

if __name__ == "__main__":
    sys.exit(main())
