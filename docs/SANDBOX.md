# Docker Sandbox for Safe Code Execution

## Overview

The Docker sandbox provides **isolated, secure code execution** using Docker containers. Code runs in ephemeral containers with resource limits and automatic cleanup.

## Features

✅ **Isolated Execution** - Code runs in separate containers  
✅ **Resource Limits** - CPU, memory, and timeout controls  
✅ **Network Isolation** - Optional network access  
✅ **Automatic Cleanup** - Containers removed after execution  
✅ **Package Installation** - Install pip packages on-the-fly  
✅ **File Operations** - Read/write files in sandbox

---

## Configuration

Add to your `.env` file:

```bash
# Sandboxing
SANDBOX_ENABLED=true
SANDBOX_TIMEOUT=30              # Execution timeout in seconds
SANDBOX_MEMORY_LIMIT=512m       # Memory limit (512m, 1g, etc.)
SANDBOX_CPU_LIMIT=1.0           # CPU limit (1.0 = 1 CPU core)
SANDBOX_NETWORK_DISABLED=true   # Disable network access
```

---

## Usage

### 1. Execute Python Code

```python
from src.middleware.sandbox import sandbox

# Simple execution
result = sandbox.execute_python("print('Hello, World!')")
print(result["stdout"])  # Hello, World!

# With packages
result = sandbox.execute_python(
    code="import requests; print(requests.get('https://api.github.com').status_code)",
    packages=["requests"]
)
```

### 2. Execute Shell Commands

```python
result = sandbox.execute_shell("ls -la /workspace")
print(result["stdout"])
```

### 3. Using LangChain Tools

```python
from src.tools.sandbox import (
    execute_python_code,
    execute_shell_command,
    test_python_code,
    check_sandbox_status
)

# Execute code
result = execute_python_code.invoke({"code": "print(2 + 2)"})
# Output: ✅ Execution successful (0.15s)\n\nOutput:\n4\n

# Test code
result = test_python_code.invoke({
    "code": "def add(a, b): return a + b",
    "test_code": "assert add(2, 3) == 5"
})

# Check status
status = check_sandbox_status.invoke({})
```

---

## Response Format

All execution methods return a dict with:

```python
{
    "success": bool,           # True if exit code == 0
    "stdout": str,             # Standard output
    "stderr": str,             # Standard error
    "exit_code": int,          # Process exit code
    "execution_time": float,   # Execution time in seconds
    "error": str               # Error message (if failed)
}
```

---

## Security Features

### 1. Resource Limits

- **CPU**: Limited to configured cores (default: 1.0)
- **Memory**: Limited to configured amount (default: 512MB)
- **Timeout**: Execution killed after timeout (default: 30s)

### 2. Network Isolation

- Network disabled by default
- Can be enabled for package installation
- No access to host network

### 3. File System

- Isolated temporary directory
- No access to host files
- Auto-deleted after execution

### 4. Container Cleanup

- Containers automatically removed
- No resource leaks
- Graceful error handling

---

## Examples

### Example 1: Data Analysis

```python
code = """
import pandas as pd
import numpy as np

data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
print(df.describe())
"""

result = sandbox.execute_python(
    code=code,
    packages=["pandas", "numpy"]
)
print(result["stdout"])
```

### Example 2: Testing Generated Code

```python
generated_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

test_code = """
assert fibonacci(0) == 0
assert fibonacci(1) == 1
assert fibonacci(5) == 5
assert fibonacci(10) == 55
print("All tests passed!")
"""

result = sandbox.execute_python(generated_code + "\n" + test_code)
```

### Example 3: File Operations

```python
code = """
# Write file
with open('/workspace/data.txt', 'w') as f:
    f.write('Hello from sandbox!')

# Read file
with open('/workspace/data.txt', 'r') as f:
    print(f.read())
"""

result = sandbox.execute_python(code)
# Output: Hello from sandbox!
```

---

## Error Handling

### Timeout

```python
code = "import time; time.sleep(60)"  # Will timeout
result = sandbox.execute_python(code)
# result["error"] = "Execution timeout after 30s"
```

### Memory Limit

```python
code = "data = [0] * (10**9)"  # Will exceed memory
result = sandbox.execute_python(code)
# Container killed, error returned
```

### Syntax Error

```python
code = "print('missing quote)"
result = sandbox.execute_python(code)
# result["success"] = False
# result["stderr"] contains error details
```

---

## Troubleshooting

### Docker Not Available

```python
if not sandbox.is_available():
    print("Docker not running!")
    # Install Docker and start daemon
```

### Permission Denied

```bash
# On Linux, add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Image Pull Fails

```bash
# Manually pull image
docker pull python:3.11-slim
```

---

## Performance

| Operation         | Time                      |
| ----------------- | ------------------------- |
| Container startup | ~2-5 seconds (first time) |
| Container startup | ~0.5-1 second (cached)    |
| Code execution    | Depends on code           |
| Container cleanup | ~0.1 seconds              |

**Optimization**: Image is cached after first pull, subsequent executions are faster.

---

## Comparison: Docker vs E2B

| Feature            | Docker Sandbox | E2B           |
| ------------------ | -------------- | ------------- |
| **Cost**           | Free           | $20-100/month |
| **Startup**        | 0.5-5s         | ~2s           |
| **Infrastructure** | Self-hosted    | Cloud-hosted  |
| **Isolation**      | Strong         | Strong        |
| **Customization**  | Full control   | Limited       |
| **Maintenance**    | You manage     | Managed       |

---

## Future Enhancements

- [ ] Container pooling for faster execution
- [ ] Support for Node.js, Go, Rust
- [ ] Persistent workspaces
- [ ] GPU support
- [ ] Multi-file projects
- [ ] Interactive REPL mode

---

## API Reference

### `DockerSandbox`

```python
class DockerSandbox:
    def __init__(
        self,
        image: str = "python:3.11-slim",
        timeout: int = 30,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        network_disabled: bool = True
    )

    def execute_python(
        self,
        code: str,
        files: Optional[Dict[str, str]] = None,
        packages: Optional[List[str]] = None
    ) -> Dict[str, Any]

    def execute_shell(
        self,
        command: str,
        working_dir: str = "/workspace"
    ) -> Dict[str, Any]

    def is_available(self) -> bool

    def get_stats(self) -> Dict[str, Any]
```

---

## Summary

✅ **Production-ready** Docker-based sandboxing  
✅ **Secure** with resource limits and isolation  
✅ **Easy to use** with LangChain tools  
✅ **Free** - no external service costs  
✅ **Flexible** - supports Python, shell, packages

**The sandbox is ready for safe code execution!** 🐳
