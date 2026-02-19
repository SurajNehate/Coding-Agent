"""Terminal tools for the coding agent."""

import os
import subprocess
from pathlib import Path
from langchain_core.tools import tool

@tool
def run_command(command: str, cwd: str | None = None) -> str:
    """
    Run a shell command in the project directory. Use for: compile, run, test, install, etc.
    Pass the full command as a string (e.g. 'uv run python main.py' or 'npm run build').
    cwd: optional subdirectory to run in (relative to project root). Default is project root.
    """
    base = Path(os.getcwd())
    work_dir = (base / cwd) if cwd else base
    if not work_dir.is_dir():
        return f"Error: Working directory '{cwd or '.'}' does not exist."
    try:
        # Use shell=True to allow command chaining and environment variable expansion
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        combined = (out + "\n" + err).strip() if (out or err) else "(no output)"
        status = f"[exit {result.returncode}]"
        return f"{status}\n{combined}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error: {e}"
