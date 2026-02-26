from __future__ import annotations

from pathlib import Path

_EXT_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
}


def get_conflicted_files(repo_path: Path) -> list[Path]:
    """Return files that Git has marked as unmerged in *repo_path*."""
    try:
        import git

        repo = git.Repo(repo_path, search_parent_directories=True)
        root = Path(repo.working_tree_dir)
        return [root / name for name in repo.index.unmerged_blobs().keys()]
    except Exception:
        return []


def detect_language(path: Path) -> str:
    """Infer a human-readable language name from *path*'s file extension."""
    return _EXT_LANGUAGE_MAP.get(path.suffix.lower(), "")
