"""Dataset validation CLI entry point (backward compatible)."""

from __future__ import annotations

import sys

from training.datasets.cli import main as cli_main

_SUBCOMMANDS = {
    "validate",
    "inspect",
    "ingest",
    "process",
    "fingerprint",
    "split",
    "report",
}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] not in _SUBCOMMANDS:
        argv = ["validate", *argv]
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
