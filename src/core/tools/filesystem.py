"""Filesystem tools for the coding agent."""

import os
from pathlib import Path
from langchain_core.tools import tool

# Directories and files to ignore when building project context
IGNORE = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    "uv.lock",
    ".gitignore",
    ".cursorignore",
}

@tool
def list_dir(path: str = ".") -> str:
    """
    List directory contents. Use '.' for current directory, or a relative path.
    Returns a string listing files and directories.
    """
    base = Path(os.getcwd())
    target = (base / path).resolve()
    if not target.exists():
        return f"Error: Path '{path}' does not exist."
    if not target.is_dir():
        return f"Error: '{path}' is not a directory."
    try:
        items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        entries = []
        for p in items:
            name = p.name
            if p.is_dir():
                entries.append(f"[dir]  {name}/")
            else:
                entries.append(f"[file] {name}")
        return "\n".join(entries) if entries else "(empty)"
    except PermissionError:
        return f"Error: Permission denied reading '{path}'."

@tool
def read_file(path: str) -> str:
    """
    Read a file and return its contents. Use a path relative to the project root.
    """
    base = Path(os.getcwd())
    target = (base / path).resolve()
    if not target.exists():
        return f"Error: File '{path}' does not exist."
    if not target.is_file():
        return f"Error: '{path}' is not a file."
    try:
        # TODO: Handle binary files better or error out
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except PermissionError:
        return f"Error: Permission denied reading '{path}'."

@tool
def write_file(path: str, content: str) -> str:
    """
    Overwrite a file with new content. Use a path relative to the project root.
    Create parent directories if they don't exist.
    """
    base = Path(os.getcwd())
    target = (base / path).resolve()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"OK: Written {len(content)} characters to '{path}'."
    except PermissionError:
        return f"Error: Permission denied writing to '{path}'."
    except Exception as e:
        return f"Error: {e}"

def _walk_tree(root: Path, prefix: str = "", max_depth: int = 4) -> list[str]:
    """Build a tree representation of the project structure."""
    lines = []
    if max_depth <= 0:
        return lines
    try:
        items = sorted(
            [p for p in root.iterdir() if p.name not in IGNORE and not p.name.startswith(".")],
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
    except PermissionError:
        return [f"{prefix}(permission denied)"]
    for i, p in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        name = p.name + "/" if p.is_dir() else p.name
        lines.append(f"{prefix}{connector}{name}")
        if p.is_dir():
            ext = "    " if is_last else "│   "
            lines.extend(_walk_tree(p, prefix + ext, max_depth - 1))
    return lines

@tool
def get_project_context(project_root: str | None = None) -> str:
    """
    Build a string describing the current project: structure and key config files.
    Used to give the agent an overview of the project before it acts.
    """
    root = Path(project_root or os.getcwd())
    parts = []

    # 1. Project structure
    tree_lines = _walk_tree(root)
    parts.append("## Project structure")
    parts.append("```")
    parts.append(root.name + "/")
    parts.extend(tree_lines)
    parts.append("```")

    # 2. Key config files
    key_files = [
        "pyproject.toml",
        "package.json",
        "requirements.txt",
        "README.md",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        ".python-version",
    ]
    found = []
    for name in key_files:
        p = root / name
        if p.is_file():
            found.append(name)

    if found:
        parts.append("\n## Key config files")
        parts.append(", ".join(found))

    # 3. Content of important config files (truncated)
    for name in ["pyproject.toml", "package.json", "requirements.txt"]:
        p = root / name
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"
                parts.append(f"\n## {name}")
                parts.append("```")
                parts.append(content)
                parts.append("```")
            except (PermissionError, OSError):
                pass

    return "\n".join(parts)
