# Token Usage Estimates

## 1. Tool Schemas

### Generator Tools

| Tool Name             | Estimated Tokens  |
| :-------------------- | :---------------- |
| `list_dir`            | ~104 tokens       |
| `read_file`           | ~82 tokens        |
| `write_file`          | ~122 tokens       |
| `run_command`         | ~202 tokens       |
| `get_project_context` | ~132 tokens       |
| `search_in_files`     | ~562 tokens       |
| `git_operations`      | ~529 tokens       |
| `find_and_replace`    | ~332 tokens       |
| **TOTAL**             | **~2,064 tokens** |

### Executor Tools

| Tool Name                 | Estimated Tokens  |
| :------------------------ | :---------------- |
| `execute_python_code`     | ~250 tokens       |
| `execute_shell_command`   | ~200 tokens       |
| `test_python_code`        | ~250 tokens       |
| `check_sandbox_status`    | ~150 tokens       |
| `execute_javascript_code` | ~250 tokens       |
| `execute_java_code`       | ~250 tokens       |
| **TOTAL**                 | **~1,350 tokens** |

---

## 2. System Prompts

| Prompt Type      | Estimated Tokens |
| :--------------- | :--------------- |
| Generator Prompt | ~140 tokens      |
| Executor Prompt  | ~100 tokens      |
| Chat Prompt      | ~65 tokens       |

---

## 3. Flow Estimates (Input Tokens)

### A. Conversational Flow ("Hello")

- Chat Prompt: ~65 tokens
- User Message: ~2 tokens
- **TOTAL: ~67 tokens**

### B. Generator Flow ("Create snake game")

- Generator Prompt: ~140 tokens
- Generator Tools: ~2,064 tokens
- User Message: ~10 tokens
- **TOTAL: ~2,214 tokens**

### C. Executor Flow (Running Code)

- Executor Prompt: ~100 tokens
- Executor Tools: ~1,350 tokens
- Context (Code + History): ~500 tokens
- **TOTAL: ~1,950 tokens**

### D. Combined Context (Late Stage)

- Generator Prompt: ~140 tokens
- Generator Tools: ~2,064 tokens
- History (10 turns): ~4,000 tokens
- **TOTAL: ~6,204 tokens**
