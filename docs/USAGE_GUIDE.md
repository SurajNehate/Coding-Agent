# AI Coding Agent - Usage Guide

## 🚀 New Features: Generator-Executor Loop

The agent now operates in a loop:

1. **Generator Agent**: Writes code using RAG, Knowledge Graph, and file tools.
2. **Executor Agent**: Runs code in a Docker Sandbox and provides feedback.
3. **Loop**: The Generator fixes code based on feedback until success or max iterations.

---

## 1. Using the Web UI (Gradio)

The easiest way to use the agent.

```bash
# Start the UI
python src/ui/app.py
```

**Access at:** `http://localhost:7860`

**Features:**

- Chat interface
- Real-time execution logs (see what the agent is doing)
- RAG integration toggle

---

## 2. Using the CLI

Run the agent from the command line for headless operation.

```bash
# Run a task
python -m src.cli run "Create a Python script to scrape a website"
```

**Options:**

- `--use-rag / --no-rag`: Enable/disable documentation search
- `--provider`: Choose LLM (openai, google)

---

## 3. Production Stack Management

Ensure all services are running before starting the agent.

```bash
# Start services (DB, Elastic, Sandbox, etc.)
docker-compose up -d

# Check status
docker-compose ps
```

---

## 4. Development & Testing

**Run Tests:**

```bash
pytest tests/
```

**Verify Sandbox:**

```bash
python -c "from src.tools.sandbox import check_sandbox_status; print(check_sandbox_status.invoke({}))"
```

---

## Troubleshooting

**Import Errors:**
If you see missing modules:

```bash
uv pip install -r requirements.txt
```

**Docker Issues:**
If the executor fails:

1. Ensure Docker Desktop is running.
2. Check containers: `docker ps`
