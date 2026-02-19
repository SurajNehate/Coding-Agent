"""
AI Coding Agent — CLI Interface
Provides commands for running the agent, initializing RAG, and launching the UI.
"""

import os
import uuid
import typer
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(
    name="coding-agent",
    help="🤖 AI Coding Agent — Multi-agent system for code generation and execution",
)


@app.command()
def run(
    task: str = typer.Argument(..., help="The coding task to execute"),
    path: str = typer.Option(".", help="Project directory"),
    provider: str = typer.Option("openai", help="LLM provider (openai, groq, ollama, anthropic)"),
    max_iters: int = typer.Option(10, help="Maximum agent iterations"),
    use_rag: bool = typer.Option(False, help="Enable RAG context"),
):
    """Run the agent on a coding task."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from src.core.agent.graph import create_graph, get_token_tracker, reset_token_tracker

    # Validate directory
    target_dir = os.path.abspath(path)
    if not os.path.exists(target_dir):
        typer.echo(f"❌ Directory not found: {target_dir}")
        raise typer.Exit(code=1)

    # Apply provider
    os.environ["DEFAULT_LLM_PROVIDER"] = provider
    reset_token_tracker()

    typer.echo(f"🚀 Task: '{task}' in '{target_dir}'")
    typer.echo(f"⚙️  Provider: {provider} | Max iterations: {max_iters}")

    # Change to target dir
    prev_dir = os.getcwd()
    os.chdir(target_dir)

    try:
        # Build RAG context
        rag_context = ""
        if use_rag:
            try:
                from src.infrastructure.rag.vector_store import rag_system
                docs = rag_system.get_context_for_query(task, k=2)
                if docs:
                    rag_context = f"\n\nRelevant Context:\n{docs}\n"
                    typer.echo("📚 RAG context loaded")
            except Exception as e:
                typer.echo(f"⚠️  RAG unavailable: {e}")

        # Build messages
        messages = [HumanMessage(content=task + rag_context)]

        inputs = {
            "messages": messages,
            "iterations": 0,
            "max_iterations": max_iters,
        }

        # Run graph
        graph = create_graph()
        start_time = datetime.now()

        typer.echo("\n" + "=" * 60)
        typer.echo("🤖 AGENT EXECUTION")
        typer.echo("=" * 60 + "\n")

        for event in graph.stream(inputs, stream_mode="values"):
            if "messages" not in event:
                continue
            msg = event["messages"][-1]

            if hasattr(msg, "content") and msg.content:
                msg_type = getattr(msg, "type", "unknown").upper()
                typer.echo(f"\n--- {msg_type} ---")
                typer.echo(msg.content)

            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    typer.echo(f"🔧 Tool: {tc['name']}")

        # Stats
        tracker = get_token_tracker()
        data = tracker.to_dict()
        elapsed = (datetime.now() - start_time).total_seconds()

        typer.echo("\n" + "=" * 60)
        typer.echo("✅ EXECUTION COMPLETE")
        typer.echo(f"⏱️  Duration: {elapsed:.1f}s")
        typer.echo(f"📊 Tokens: {data['total_tokens']:,} ({data['llm_calls']} calls)")
        typer.echo("=" * 60)

    except KeyboardInterrupt:
        typer.echo("\n⚠️ Interrupted.")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        os.chdir(prev_dir)


@app.command()
def ui():
    """Launch the Streamlit web UI."""
    import subprocess
    import sys

    ui_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    typer.echo("🌐 Launching Streamlit UI...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path, "--server.headless", "true"])


@app.command()
def init_rag(
    docs_dir: str = typer.Option("data/documents", help="Directory containing documents"),
):
    """Initialize the RAG system with documents."""
    from src.infrastructure.rag.vector_store import rag_system

    typer.echo(f"📚 Initializing RAG from: {docs_dir}")

    if not os.path.exists(docs_dir):
        typer.echo(f"❌ Directory not found: {docs_dir}")
        raise typer.Exit(code=1)

    try:
        documents = rag_system.load_documents_from_directory(docs_dir)
        typer.echo(f"📄 Loaded {len(documents)} documents")

        ids = rag_system.add_documents(documents)
        typer.echo(f"✅ Added {len(ids)} chunks to vector store")

        stats = rag_system.get_collection_stats()
        typer.echo(f"📊 Total chunks: {stats['document_count']}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()