# Data Directory

This directory stores input data for the AI Coding Agent.

## Structure

```
data/
├── documents/          # Input documents for RAG system (pdf, txt, md)
```

## Usage

### RAG (Retrieval Augmented Generation)

1.  **Add Documents**: place your documentation files in `data/documents/`.
    - Supported formats: `.pdf`, `.md`, `.txt`
2.  **Initialize Index**: Run the CLI command to ingest documents.
    ```bash
    python src/main.py cli init-rag --docs-dir ./data/documents
    ```

### Persistence

- **Vector Store (Qdrant)**: Stored in Docker volume `qdrant_data`.
- **Conversation History (Postgres)**: Stored in Docker volume `postgres_data`.

> Note: Local database files (`chroma_db`, `qdrant_db`) are no longer used. You can safely delete them if they exist.
