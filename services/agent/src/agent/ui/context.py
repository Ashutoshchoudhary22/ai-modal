"""Build UI repository context using existing index/search."""

from __future__ import annotations

from pathlib import Path

from ai_platform_protocol.ui import UIFrameworkProfile, UIRepositoryContext
from code_indexer.loader import load_index_data

from agent.config import UISettings
from agent.ui.detector import detect_framework_profile
from agent.ui.tokens import extract_design_tokens

COMPONENT_NAMES = (
    "Button",
    "Input",
    "Card",
    "Modal",
    "Navbar",
    "Sidebar",
    "Form",
    "Table",
    "Tabs",
    "Dialog",
    "Hero",
)


def build_ui_context(
    workspace_root: Path,
    *,
    settings: UISettings | None = None,
    profile: UIFrameworkProfile | None = None,
) -> UIRepositoryContext:
    root = workspace_root.resolve()
    profile = profile or detect_framework_profile(root)
    cfg = UISettings() if settings is None else settings
    files, symbols, _, _ = load_index_data(root, workspace_id="ui-context")

    components: list[str] = []
    pages: list[str] = []
    layouts: list[str] = []
    relevant: list[str] = []

    for symbol in symbols:
        name = symbol.name
        path = getattr(symbol, "file_path", None) or getattr(symbol, "relative_path", "")
        if any(c.lower() in name.lower() for c in COMPONENT_NAMES):
            components.append(f"{name} ({path})")
        if "page" in path.lower() or "Page" in name:
            pages.append(path)
        if "layout" in path.lower() or "Layout" in name:
            layouts.append(path)
        relevant.append(path)

    if profile.component_directory:
        comp_dir = root / profile.component_directory
        if comp_dir.is_dir():
            for path in sorted(comp_dir.rglob("*.tsx"))[: cfg.max_components]:
                rel = str(path.relative_to(root)).replace("\\", "/")
                name = path.stem
                entry = f"{name} ({rel})"
                if entry not in components:
                    components.append(entry)
                if rel not in relevant:
                    relevant.append(rel)

    relevant = list(dict.fromkeys(relevant))[: cfg.max_files]
    tokens = extract_design_tokens(root, profile)

    return UIRepositoryContext(
        framework=profile,
        components=components[: cfg.max_components],
        pages=list(dict.fromkeys(pages))[: cfg.max_files],
        layouts=list(dict.fromkeys(layouts))[: cfg.max_files],
        design_tokens=tokens,
        relevant_files=relevant,
    )
