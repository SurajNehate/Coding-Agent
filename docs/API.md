# API Documentation

## Overview

The Coding Agent API provides a RESTful interface with WebSocket support for real-time interaction with the AI coding agent. The API includes authentication, task management, knowledge graph queries, and session management.

## Base URL

```
http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Get Access Token

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### Health Check

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-02-09T15:30:00",
  "services": {
    "api": "up",
    "database": "up",
    "knowledge_graph": "up"
  }
}
```

### Submit Task

```http
POST /api/v1/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "task": "Analyze the code and find bugs",
  "user_id": "john_doe",
  "session_id": "session-123",
  "project_path": "/path/to/project",
  "use_rag": true,
  "provider": "openai"
}
```

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Task submitted successfully"
}
```

### Get Task Status

```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": "Analysis complete. Found 3 potential bugs...",
  "created_at": "2024-02-09T15:30:00",
  "updated_at": "2024-02-09T15:32:00"
}
```

### Build Knowledge Graph

```http
POST /api/v1/graph/build
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_path": "/path/to/project",
  "file_extensions": [".py", ".js"]
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Knowledge graph built successfully",
  "stats": {
    "files": 45,
    "classes": 23,
    "functions": 156,
    "imports": 89,
    "relationships": 312
  }
}
```

### Query Knowledge Graph

```http
POST /api/v1/graph/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query_type": "usages",
  "target": "process_data",
  "depth": 3
}
```

**Query Types:**

- `usages` - Find function usages
- `hierarchy` - Get class hierarchy
- `dependencies` - Get file dependencies
- `circular` - Find circular imports
- `callgraph` - Get function call graph

**Response:**

```json
{
  "status": "success",
  "query_type": "usages",
  "results": [
    {
      "caller": "main",
      "callee": "process_data",
      "count": 2
    }
  ]
}
```

### Get Graph Statistics

```http
GET /api/v1/graph/stats
Authorization: Bearer <token>
```

**Response:**

```json
{
  "status": "success",
  "stats": {
    "files": 45,
    "classes": 23,
    "functions": 156,
    "modules": 34,
    "relationships": 312
  }
}
```

### List Sessions

```http
GET /api/v1/sessions?user_id=john_doe&limit=10
Authorization: Bearer <token>
```

**Response:**

```json
{
  "status": "success",
  "sessions": [
    {
      "id": "session-123",
      "user_id": "john_doe",
      "created_at": "2024-02-09T15:00:00",
      "updated_at": "2024-02-09T15:30:00",
      "metadata": {}
    }
  ]
}
```

### Get Metrics

```http
GET /api/v1/metrics
```

Returns Prometheus-formatted metrics.

### WebSocket Streaming

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/stream");

ws.onopen = () => {
  ws.send(
    JSON.stringify({
      task: "Analyze the code",
      user_id: "john_doe",
    }),
  );
};

ws.onmessage = (event) => {
  console.log("Received:", event.data);
};
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

**Error Format:**

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

API requests are rate-limited to 60 requests per minute per user.

## Examples

### Python Example

```python
import requests

# Get token
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={"username": "admin", "password": "admin"}
)
token = response.json()["access_token"]

# Submit task
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/v1/tasks",
    headers=headers,
    json={
        "task": "Analyze the code",
        "user_id": "john_doe"
    }
)
task_id = response.json()["task_id"]

# Check status
response = requests.get(
    f"http://localhost:8000/api/v1/tasks/{task_id}",
    headers=headers
)
print(response.json())
```

### cURL Example

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=admin" | jq -r .access_token)

# Submit task
TASK_ID=$(curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"Analyze code","user_id":"john"}' | jq -r .task_id)

# Check status
curl http://localhost:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.
