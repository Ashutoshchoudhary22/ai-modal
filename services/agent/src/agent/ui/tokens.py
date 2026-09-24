"""Lightweight design token extraction."""

from __future__ import annotations

import re
from pathlib import Path

from ai_platform_protocol.ui import UIFrameworkProfile


def extract_design_tokens(
    workspace_root: Path, profile: UIFrameworkProfile
) -> dict[str, list[str]]:
    tokens: dict[str, list[str]] = {
        "colors": [],
        "spacing": [],
        "fonts": [],
        "css_variables": [],
    }
    for rel in profile.design_token_files:
        path = workspace_root / rel
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        tokens["css_variables"].extend(re.findall(r"--[\w-]+", content))
        if "tailwind" in rel:
            tokens["colors"].extend(re.findall(r"colors:\s*\{([^}]+)\}", content))
        tokens["fonts"].extend(re.findall(r"fontFamily:\s*\{([^}]+)\}", content))
    for rel in profile.design_token_files:
        if rel.endswith(".css"):
            path = workspace_root / rel
            content = path.read_text(encoding="utf-8", errors="replace")
            tokens["colors"].extend(re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", content))
    return {k: list(dict.fromkeys(v))[:20] for k, v in tokens.items() if v}
