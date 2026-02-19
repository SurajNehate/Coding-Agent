# 📊 Observability & Monitoring Guide

This guide details how to monitor the AI Coding Agent during runtime and analyze execution after completion.

## 🚀 Runtime Monitoring (Real-time)

| Service          | URL                                              | Description                                                                                                             |
| ---------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **Gradio UI**    | [http://localhost:7860](http://localhost:7860)   | **Primary Interface**. View real-time agent "thoughts", tool calls, and execution logs in the right-hand panel.         |
| **Jaeger UI**    | [http://localhost:16686](http://localhost:16686) | **Distributed Tracing**. View the timeline of requests, including database calls and internal service latency.          |
| **Flower**       | [http://localhost:5555](http://localhost:5555)   | **Task Queue**. Monitor background async tasks (Celery). Useful if the agent offloads heavy work to background workers. |
| **Docker Stats** | `docker stats`                                   | **Resource Usage**. Monitor CPU/Memory usage of the sandboxed environments and infrastructure containers.               |

### 🔍 Deep Dive: Jaeger Tracing

Use Jaeger to debug performance bottlenecks.

1. Open [Jaeger UI](http://localhost:16686).
2. Select `coding-agent-api` or `coding-agent-worker` from the **Service** dropdown.
3. Click **Find Traces** to see recent operations.

---

## 📈 Post-Execution Analysis (History & Debugging)

| Service           | URL                                                                          | Description                                                                                                                                  |
| ----------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Langfuse**      | [https://cloud.langfuse.com](https://cloud.langfuse.com)                     | **LLM Tracing**. The _best_ tool for inspecting agent logic. View full prompt/response history, token usage, and latency for every LLM call. |
| **Neo4j Browser** | [http://localhost:7474](http://localhost:7474)                               | **Knowledge Graph**. Explore the agent's understanding of the codebase. Login with `neo4j` / `password`.                                     |
| **API Metrics**   | [http://localhost:8000/api/v1/metrics](http://localhost:8000/api/v1/metrics) | **Prometheus Metrics**. Raw metrics data for scraping.                                                                                       |

### 🧠 Deep Dive: Langfuse

Langfuse provides the most detailed insight into the "mind" of the agent.

1. Log in to [Langfuse Cloud](https://cloud.langfuse.com).
2. Your `.env` is configured with project keys.
3. Look for the project associated with the keys `pk-lf-...` and `sk-lf-...`.
4. **Traces** view shows the nested execution graph (Agent -> Graph -> LLM -> Tool).

---

## 🛠️ Infrastructure Status

You can check the health of all services using Docker:

```bash
docker-compose ps
```

**Expected Status:**

- `coding-agent-api`: Up (Port 8000)
- `coding-agent-jaeger`: Up (Port 16686)
- `coding-agent-flower`: Up (Port 5555)
- `coding-agent-neo4j`: Up (Port 7474)
- `coding-agent-redis`: Up
- `coding-agent-postgres`: Up
