"""Search and Git tools for the coding agent."""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool


# Directories to skip during search
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".eggs",
    "*.egg-info", ".tox", ".mypy_cache", ".pytest_cache",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".o", ".a", ".dll", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".lock", ".map",
}


def _should_skip_dir(name: str) -> bool:
    """Check if directory should be skipped."""
    return name in SKIP_DIRS or name.startswith(".")


def _should_skip_file(name: str) -> bool:
    """Check if file should be skipped based on extension."""
    _, ext = os.path.splitext(name)
    return ext.lower() in SKIP_EXTENSIONS


@tool
def search_in_files(
    query: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    max_results: int = 30,
) -> str:
    """Search for a text pattern across files in the project directory.

    This is a grep-like tool. Use it to find function definitions, class usages,
    imports, string literals, TODO comments, error messages, etc.

    Args:
        query: Text or pattern to search for (plain text, not regex)
        path: Directory to search in (relative to project root). Default: project root
        file_pattern: Optional filter like '*.py', '*.js', '*.ts'. Default: all code files
        case_sensitive: Whether to match case. Default: False (case-insensitive)
        max_results: Maximum number of matching lines to return. Default: 30

    Returns:
        Matching lines with file path and line number, or a message if no matches.

    Example:
        search_in_files("def create_graph")
        search_in_files("TODO", file_pattern="*.py")
        search_in_files("import requests", path="src")
    """
    base = Path(os.getcwd())
    target = (base / path).resolve()

    if not target.exists():
        return f"Error: Path '{path}' does not exist."
    if not target.is_file() and not target.is_dir():
        return f"Error: '{path}' is not a file or directory."

    # Determine valid extensions from pattern
    valid_extensions = None
    if file_pattern:
        # e.g., "*.py" → ".py"
        if file_pattern.startswith("*"):
            valid_extensions = {file_pattern[1:]}  # {".py"}
        else:
            valid_extensions = {file_pattern}

    results = []

    if target.is_file():
        files_to_search = [target]
    else:
        files_to_search = []
        for root_dir, dirs, files in os.walk(target):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
            for fname in files:
                if _should_skip_file(fname):
                    continue
                if valid_extensions:
                    _, ext = os.path.splitext(fname)
                    if ext.lower() not in valid_extensions:
                        continue
                files_to_search.append(Path(root_dir) / fname)

    for fpath in files_to_search:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    matched = False
                    if case_sensitive:
                        matched = query in line
                    else:
                        matched = query.lower() in line.lower()

                    if matched:
                        rel = fpath.relative_to(base)
                        results.append(f"{rel}:{line_num}: {line.rstrip()}")
                        if len(results) >= max_results:
                            break
        except (PermissionError, OSError):
            continue

        if len(results) >= max_results:
            break

    if not results:
        return f"No matches found for '{query}'."

    header = f"Found {len(results)} match(es) for '{query}':\n"
    truncation_note = ""
    if len(results) >= max_results:
        truncation_note = f"\n... (results capped at {max_results})"

    return header + "\n".join(results) + truncation_note


@tool
def git_operations(operation: str, args: Optional[str] = None) -> str:
    """Perform Git operations in the project repository.

    Args:
        operation: Git operation to perform. One of:
            - "status"  — Show working tree status (modified, staged, untracked)
            - "diff"    — Show unstaged changes (or staged with args="--staged")
            - "log"     — Show recent commit history (default: last 10 commits)
            - "branch"  — List branches and show current branch
            - "show"    — Show details of a specific commit (pass commit hash in args)
            - "blame"   — Show line-by-line authorship of a file (pass file path in args)
        args: Optional additional arguments for the operation

    Returns:
        Git command output

    Example:
        git_operations("status")
        git_operations("log", args="-5 --oneline")
        git_operations("diff", args="--staged")
        git_operations("blame", args="src/agent/graph.py")
    """
    base = Path(os.getcwd())

    # Check if it's a git repo
    if not (base / ".git").exists():
        return "Error: Not a Git repository."

    # Build the command based on operation
    allowed_operations = {"status", "diff", "log", "branch", "show", "blame"}
    operation = operation.strip().lower()

    if operation not in allowed_operations:
        return f"Error: Unknown operation '{operation}'. Allowed: {', '.join(sorted(allowed_operations))}"

    cmd = ["git", operation]

    # Add default args for some operations
    if operation == "log" and not args:
        cmd.extend(["--oneline", "-n", "10"])
    elif operation == "branch" and not args:
        cmd.extend(["-a"])
    elif operation == "diff" and not args:
        pass  # default: unstaged changes

    # Append user-specified args
    if args:
        cmd.extend(args.split())

    try:
        result = subprocess.run(
            cmd,
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        combined = (out + "\n" + err).strip() if (out or err) else "(no output)"

        # Truncate very long output
        if len(combined) > 5000:
            combined = combined[:5000] + "\n... (output truncated)"

        return f"[git {operation}] (exit {result.returncode})\n{combined}"
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out after 30 seconds."
    except FileNotFoundError:
        return "Error: Git is not installed or not in PATH."
    except Exception as e:
        return f"Error: {e}"


@tool
def find_and_replace(
    file_path: str,
    find_text: str,
    replace_text: str,
    count: int = 0,
) -> str:
    """Find and replace text in a file. Useful for making targeted code edits.

    Args:
        file_path: Path to the file (relative to project root)
        find_text: Exact text to find
        replace_text: Text to replace it with
        count: Maximum number of replacements. 0 means replace all occurrences.

    Returns:
        Confirmation of how many replacements were made

    Example:
        find_and_replace("src/main.py", "old_function_name", "new_function_name")
    """
    base = Path(os.getcwd())
    target = (base / file_path).resolve()

    if not target.exists():
        return f"Error: File '{file_path}' does not exist."
    if not target.is_file():
        return f"Error: '{file_path}' is not a file."

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

    occurrences = content.count(find_text)
    if occurrences == 0:
        return f"No occurrences of the search text found in '{file_path}'."

    if count > 0:
        new_content = content.replace(find_text, replace_text, count)
        replacements = min(count, occurrences)
    else:
        new_content = content.replace(find_text, replace_text)
        replacements = occurrences

    try:
        target.write_text(new_content, encoding="utf-8")
        return f"OK: Replaced {replacements} occurrence(s) in '{file_path}'."
    except Exception as e:
        return f"Error writing file: {e}"
