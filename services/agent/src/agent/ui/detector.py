"""Framework and styling detection from repository inspection."""

from __future__ import annotations

import json
from pathlib import Path

from ai_platform_protocol.ui import StylingSystem, UIFramework, UIFrameworkProfile


def detect_framework_profile(workspace_root: Path) -> UIFrameworkProfile:
    root = workspace_root.resolve()
    package_json = _read_package_json(root)
    deps = _merge_deps(package_json)
    framework = _detect_framework(root, deps)
    styling = _detect_styling(root, deps)
    language = "typescript" if _has_typescript(root) else "javascript"
    component_dir, page_dir = _detect_directories(root, framework)
    scripts = package_json.get("scripts", {}) if package_json else {}

    return UIFrameworkProfile(
        framework=framework,
        language=language,
        routing=_detect_routing(framework),
        styling_system=styling,
        component_directory=component_dir,
        page_directory=page_dir,
        entry_points=_detect_entry_points(root, framework),
        build_command=_script(scripts, ("build",)),
        test_command=_script(scripts, ("test",)),
        dev_command=_script(scripts, ("dev", "start")),
        ui_libraries=_detect_ui_libraries(deps),
        design_token_files=_find_design_token_files(root),
    )


def _read_package_json(root: Path) -> dict:
    path = root / "package.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _merge_deps(package_json: dict) -> dict[str, str]:
    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = package_json.get(key, {})
        if isinstance(section, dict):
            deps.update(section)
    return deps


def _detect_framework(root: Path, deps: dict[str, str]) -> UIFramework:
    if "next" in deps:
        if (root / "app").is_dir():
            return UIFramework.NEXTJS_APP
        if (root / "pages").is_dir():
            return UIFramework.NEXTJS_PAGES
        return UIFramework.NEXTJS_APP
    if "vite" in deps and "react" in deps:
        return UIFramework.VITE_REACT
    if "react" in deps or "react-dom" in deps:
        return UIFramework.REACT
    if (root / "src" / "App.tsx").exists() or (root / "src" / "App.jsx").exists():
        return UIFramework.VITE_REACT
    return UIFramework.UNKNOWN


def _detect_styling(root: Path, deps: dict[str, str]) -> StylingSystem:
    if "tailwindcss" in deps or any(root.glob("tailwind.config.*")):
        return StylingSystem.TAILWIND
    if "styled-components" in deps:
        return StylingSystem.STYLED_COMPONENTS
    if "sass" in deps or any(root.rglob("*.scss")):
        return StylingSystem.SCSS
    if any(root.rglob("*.module.css")):
        return StylingSystem.CSS_MODULES
    if any(root.rglob("*.css")):
        return StylingSystem.PLAIN_CSS
    return StylingSystem.UNKNOWN


def _has_typescript(root: Path) -> bool:
    return (root / "tsconfig.json").exists() or any(root.rglob("*.tsx"))


def _detect_directories(root: Path, framework: UIFramework) -> tuple[str | None, str | None]:
    candidates_components = [
        "src/components",
        "components",
        "app/components",
        "src/ui",
        "components/ui",
    ]
    candidates_pages = ["app", "pages", "src/pages", "src/routes"]
    component_dir = next((p for p in candidates_components if (root / p).is_dir()), None)
    page_dir = None
    if framework in {UIFramework.NEXTJS_APP, UIFramework.NEXTJS_PAGES}:
        page_dir = "app" if framework == UIFramework.NEXTJS_APP else "pages"
    else:
        page_dir = next((p for p in candidates_pages if (root / p).is_dir()), None)
    return component_dir, page_dir


def _detect_routing(framework: UIFramework) -> str:
    mapping = {
        UIFramework.NEXTJS_APP: "next_app_router",
        UIFramework.NEXTJS_PAGES: "next_pages_router",
        UIFramework.VITE_REACT: "client_router",
        UIFramework.REACT: "client_router",
    }
    return mapping.get(framework, "unknown")


def _detect_entry_points(root: Path, framework: UIFramework) -> list[str]:
    entries = []
    for candidate in ("src/main.tsx", "src/main.ts", "src/index.tsx", "src/App.tsx"):
        if (root / candidate).exists():
            entries.append(candidate)
    if framework == UIFramework.NEXTJS_APP and (root / "app" / "layout.tsx").exists():
        entries.append("app/layout.tsx")
    return entries


def _script(scripts: dict, names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in scripts:
            return f"npm run {name}"
    return None


def _detect_ui_libraries(deps: dict[str, str]) -> list[str]:
    libraries = []
    for key in (
        "@mui/material",
        "@chakra-ui/react",
        "antd",
        "@radix-ui/react-dialog",
        "@radix-ui/react-slot",
    ):
        if key in deps:
            libraries.append(key)
    if any(k.startswith("@/components/ui") for k in deps):
        libraries.append("shadcn/ui")
    return libraries


def _find_design_token_files(root: Path) -> list[str]:
    patterns = (
        "tailwind.config.*",
        "src/styles/globals.css",
        "src/index.css",
        "styles/globals.css",
        "theme.ts",
        "theme.js",
        "src/theme.ts",
    )
    found: list[str] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                found.append(str(path.relative_to(root)).replace("\\", "/"))
    return found[:10]
