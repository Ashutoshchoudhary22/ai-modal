"""Binary file detection."""

from __future__ import annotations

from pathlib import Path

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".kt",
    ".swift",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".sql",
    ".sh",
    ".ps1",
    ".toml",
    ".xml",
    ".txt",
    ".ini",
    ".cfg",
    ".env.example",
}


def is_binary_content(data: bytes, max_sample: int = 8192) -> bool:
    sample = data[:max_sample]
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    text_chars = sum(1 for byte in sample if byte in (9, 10, 13) or 32 <= byte <= 126)
    return (text_chars / len(sample)) < 0.85


def is_binary_file(path: Path, data: bytes | None = None) -> bool:
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        if data is None:
            return False
        return is_binary_content(data)
    if data is None:
        try:
            with path.open("rb") as handle:
                data = handle.read(8192)
        except OSError:
            return True
    return is_binary_content(data)
