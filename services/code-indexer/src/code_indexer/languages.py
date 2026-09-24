"""Language detection registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LanguageInfo:
    id: str
    extensions: frozenset[str]
    parser_available: bool = True


EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "shell",
    ".ps1": "powershell",
}


PARSER_LANGUAGES = frozenset({"python", "javascript", "typescript", "tsx", "jsx"})


class LanguageRegistry:
    def detect(self, path: Path, content: str | None = None) -> LanguageInfo | None:
        ext = path.suffix.lower()
        lang_id = EXTENSION_MAP.get(ext)
        if lang_id is None:
            return None
        if lang_id == "jsx":
            lang_id = "javascript"
        if lang_id == "tsx":
            lang_id = "typescript"
        parser_available = lang_id in PARSER_LANGUAGES
        return LanguageInfo(
            id=lang_id,
            extensions=frozenset({ext}),
            parser_available=parser_available,
        )

    def has_parser(self, language_id: str) -> bool:
        return language_id in PARSER_LANGUAGES
