"""
Unified Entry Point for AI Coding Agent.
Launch with:
  python src/main.py ui       # Streamlit
  python src/main.py api      # FastAPI
  python src/main.py cli      # Typer CLI
"""
import sys
import os
import subprocess

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/main.py [ui|api|cli] [args...]")
        sys.exit(1)

    mode = sys.argv[1]
    args = sys.argv[2:]

    if mode == "ui":
        run_ui(args)
    elif mode == "api":
        run_api(args)
    elif mode == "cli":
        run_cli(args)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

def run_ui(args):
    print("🚀 Launching Streamlit UI...")
    path = os.path.join("src", "interfaces", "ui", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", path] + args)

def run_api(args):
    print("🚀 Launching FastAPI Server...")
    subprocess.run([sys.executable, "-m", "uvicorn", "src.interfaces.api.main:app", "--reload"] + args)

def run_cli(args):
    # For CLI, we import and run the Typer app directly
    # Need to adjust sys.argv so Typer processes the subcommands correctly
    sys.argv = ["coding-agent"] + args
    from src.interfaces.cli.main import app
    app()

if __name__ == "__main__":
    main()
