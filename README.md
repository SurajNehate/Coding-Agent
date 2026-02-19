# 🤖 AI Coding Agent

**Production-grade multi-agent system for code generation, execution, and analysis.**

Built with **LangGraph**, **LangChain**, and **Streamlit** — designed with a clean, segregated, interface-agnostic architecture.

---

## 🏗️ Architecture

The project is organized into three distinct layers:

```text
src/
├── core/                   # 🧠 Interface-Agnostic "Brain"
│   ├── agent/              # LangGraph Logic (Generator/Executor loop & State)
│   ├── logic/              # Business Logic (LLM Factory)
│   └── tools/              # Tool Definitions (Filesystem, Terminal, Sandbox)
├── infrastructure/         # 🏗️ Heavy Services & Integrations
│   ├── sandbox/            # Docker Execution Environment Manager
│   ├── persistence/        # Persistance Layer (Postgres)
│   ├── observability/      # Tracing (Langfuse) & Metrics (Prometheus)
│   ├── security/           # Guardrails & Validation
│   └── rag/                # Vector Store (Qdrant)
└── interfaces/             # 🔌 Entry Points
    ├── ui/                 # Streamlit App (Lite Mode - Single User)
    ├── api/                # FastAPI Server (Production Mode - Multi User)
    └── cli/                # Command Line Tools (Headless / Utils)
```

### Operational Modes

| Mode           | Command                  | Description                                                                                                                   |
| :------------- | :----------------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| **UI (Lite)**  | `python src/main.py ui`  | **Streamlit** interface. Runs locally with in-memory state. Fast start, ideal for single-user development or local debugging. |
| **API (Prod)** | `python src/main.py api` | **FastAPI** server. Supports multi-tenancy, JWT auth, and persistent PostgreSQL state. Designed for deployment.               |
| **CLI**        | `python src/main.py cli` | Terminal commands for headless task execution and managing RAG documents.                                                     |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Docker** (Required for the code execution sandbox)
- API key for an LLM provider (OpenAI, Anthropic, Groq, or Ollama)

### Setup

1.  **Clone & Install**

    ```bash
    git clone <repo-url>
    cd coding-agent
    python -m pip install -r requirements.txt
    ```

2.  **Configure Environment**

    ```bash
    cp .env.example .env
    # Open .env and add your API keys (e.g., OPENAI_API_KEY)
    ```

3.  **Launch**
    - **For Visual Interface:**
      ```bash
      python src/main.py ui
      # Opens http://localhost:8501
      ```
    - **For Production API (with Docker Compose):**
      ```bash
      docker-compose up --build
      # API at http://localhost:8000
      # Qdrant Dashboard at http://localhost:6333/dashboard
      ```

---

## 📂 Key Components

### Core Agent (`src/core/`)

The brain of the operation. Defines a robust `Generator` → `Executor` feedback loop.

- **Generator Agent**: Writes and modifies code using comprehensive file and search tools.
- **Executor Agent**: Validates code by running it in a secure Docker sandbox.
- **Smart Router**: Intelligently routes casual conversation to a cheap prompt vs. complex coding tasks to the full agent loop, saving tokens.

### Infrastructure (`src/infrastructure/`)

Pluggable backend services.

- **Sandbox**: Manages isolated Docker containers for safe code execution.
- **Persistence**: Adapter for PostgreSQL (active in API mode).
- **Observability**: Integrations for Langfuse (tracing) and Prometheus (metrics).
- **RAG**: Qdrant-based retrieval for project documentation (replaces ChromaDB).

---

## 🛠️ Agent Tools

The agents are equipped with the following tools to autonomously complete tasks:

### Generator Tools

| Tool               | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `list_dir`         | List files and directories                  |
| `read_file`        | Read the contents of a file                 |
| `write_file`       | Create or update files                      |
| `run_command`      | Execute terminal commands (outside sandbox) |
| `search_in_files`  | Grep-like search across the codebase        |
| `git_operations`   | Check git status, diffs, and logs           |
| `find_and_replace` | Precise text replacement in files           |

### Executor Tools

| Tool                    | Purpose                                        |
| ----------------------- | ---------------------------------------------- |
| `execute_python_code`   | Run Python scripts in the sandbox              |
| `test_python_code`      | Run pytest suites in the sandbox               |
| `execute_shell_command` | Run shell commands inside the sandbox          |
| `check_sandbox_status`  | Verify the health of the execution environment |

---

## 📜 License

MIT
