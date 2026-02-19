"""
AI Coding Agent — LangGraph Orchestration
Production-grade Generator-Executor loop with tool routing,
token tracking, smart routing, and Langfuse tracing.
"""

import os
import time
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from src.core.agent.state import AgentState
from src.core.tools.filesystem import list_dir, read_file, write_file, get_project_context
from src.core.tools.terminal import run_command
from src.core.tools.search import search_in_files, git_operations, find_and_replace
from src.core.tools.sandbox import (
    execute_python_code,
    test_python_code,
    execute_shell_command,
    execute_javascript_code,
    execute_java_code,
    check_sandbox_status,
)
from src.core.logic.llm import get_llm

from dotenv import load_dotenv
load_dotenv()


# ──────────────────────────────────────────────
#  Token Usage Tracking
# ──────────────────────────────────────────────

class TokenUsageHandler(BaseCallbackHandler):
    """Track token usage across LLM calls."""

    def __init__(self):
        super().__init__()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        self.model_name = ""

    def on_llm_end(self, response, **kwargs):
        self.total_calls += 1
        try:
            if hasattr(response, "llm_output") and response.llm_output:
                usage = response.llm_output.get("token_usage", {})
                self.total_input_tokens += usage.get("prompt_tokens", 0)
                self.total_output_tokens += usage.get("completion_tokens", 0)
                self.model_name = response.llm_output.get("model_name", self.model_name)
            if hasattr(response, "generations") and response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, "generation_info") and gen.generation_info:
                            usage = gen.generation_info.get("usage_metadata", {})
                            if usage:
                                self.total_input_tokens += usage.get("input_tokens", 0)
                                self.total_output_tokens += usage.get("output_tokens", 0)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "llm_calls": self.total_calls,
            "model": self.model_name,
        }


_token_tracker = TokenUsageHandler()


def get_token_tracker() -> TokenUsageHandler:
    return _token_tracker


def reset_token_tracker():
    global _token_tracker
    _token_tracker = TokenUsageHandler()


# ──────────────────────────────────────────────
#  Langfuse Integration (lazy — pydantic v1 compat)
# ──────────────────────────────────────────────

_LangfuseCallbackHandler = None


def _get_langfuse_handler():
    """Lazily import and return a Langfuse CallbackHandler, or None on failure."""
    global _LangfuseCallbackHandler
    if _LangfuseCallbackHandler is None:
        try:
            from langfuse.langchain import CallbackHandler
            _LangfuseCallbackHandler = CallbackHandler
        except Exception:
            _LangfuseCallbackHandler = False
    if _LangfuseCallbackHandler is False:
        return None
    try:
        return _LangfuseCallbackHandler()
    except Exception:
        return None


# ──────────────────────────────────────────────
#  Tools
# ──────────────────────────────────────────────

GENERATOR_TOOLS = [
    list_dir, read_file, write_file, run_command,
    get_project_context, search_in_files, git_operations, find_and_replace,
]

EXECUTOR_TOOLS = [
    execute_python_code, test_python_code, execute_shell_command,
    execute_javascript_code, execute_java_code, check_sandbox_status,
]


# ──────────────────────────────────────────────
#  LLM Factory
# ──────────────────────────────────────────────

def get_model(provider: str = "openai", temperature: float = 0):
    """Get the LLM with token-tracking and optional Langfuse callbacks."""
    provider = os.getenv("DEFAULT_LLM_PROVIDER", provider)
    callbacks = [_token_tracker]

    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        handler = _get_langfuse_handler()
        if handler:
            callbacks.append(handler)

    try:
        return get_llm(provider=provider, temperature=temperature, callbacks=callbacks)
    except Exception as e:
        print(f"[LLM] Error initializing {provider}: {e}. Fallback to OpenAI.")
        return get_llm(provider="openai", temperature=temperature, callbacks=callbacks)


# ──────────────────────────────────────────────
#  System Prompts (concise to reduce token usage)
# ──────────────────────────────────────────────

GENERATOR_PROMPT = """\
You are the Generator Agent — an expert software engineer.
Write high-quality, bug-free code based on the user's request.

Tools: list_dir, read_file, write_file, run_command, get_project_context, search_in_files, git_operations, find_and_replace.

Workflow:
1. Understand the request. Use read tools to inspect existing code.
2. Write or modify code using write_file / find_and_replace.
3. When code is READY to execute, respond with READY_FOR_EXECUTION.
4. If you receive execution feedback with errors, fix them.

Rules:
- Produce complete, runnable code (no placeholders).
- Include error handling and docstrings.
- Always end with READY_FOR_EXECUTION when code is complete.\
"""

EXECUTOR_PROMPT = """\
You are the Executor Agent — a code testing specialist.
Execute generated code and report results.

Tools: execute_python_code, test_python_code, execute_shell_command, execute_javascript_code, execute_java_code, check_sandbox_status.

Workflow:
1. Execute code with the appropriate tool.
2. If successful: respond with "SUCCESS" and include output.
3. If failed: provide the exact error, failing line, and fix suggestion.\
"""

CHAT_PROMPT = """\
You are an expert AI coding assistant. The user is chatting casually.
Respond naturally and concisely. If asked about capabilities, mention:
code generation, execution, project analysis, file operations, git, search.
Keep responses short and friendly.\
"""


# ──────────────────────────────────────────────
#  Smart Routing
# ──────────────────────────────────────────────

_TASK_KEYWORDS = {
    "create", "write", "build", "make", "implement", "generate", "code",
    "fix", "debug", "refactor", "modify", "update", "change", "edit",
    "delete", "remove", "add", "install", "run", "execute", "test",
    "deploy", "analyze", "scan", "search", "find", "replace", "read",
    "file", "directory", "folder", "function", "class", "module",
    "api", "server", "database", "script", "program", "app",
    "error", "bug", "issue", "crash", "exception", "traceback",
    "import", "package", "dependency", "pip", "npm", "git",
    "python", "javascript", "java", "html", "css", "sql",
    "project", "structure", "architecture", "config", "setup",
    "list", "show", "print", "log", "save", "load", "parse",
}


def _is_conversational(text: str) -> bool:
    """True if the message is casual chat, False if it needs tools."""
    if not text:
        return True
    clean = text.strip().lower()
    if len(clean.split()) <= 3:
        words = set(clean.replace("?", "").replace("!", "").replace(".", "").split())
        if not words & _TASK_KEYWORDS:
            return True
    _CHAT_PATTERNS = [
        "hello", "hi ", "hi!", "hey", "howdy", "greetings",
        "good morning", "good afternoon", "good evening",
        "thank", "thanks", "thx", "ty",
        "who are you", "what are you", "what can you do",
        "how are you", "what's up", "whats up",
        "nice", "cool", "great", "awesome", "ok", "okay",
        "yes", "no", "sure", "nope", "yep", "yeah",
        "explain", "tell me about", "describe", "what is",
    ]
    for pat in _CHAT_PATTERNS:
        if clean.startswith(pat) or clean == pat.rstrip():
            remainder_words = set(clean[len(pat):].strip().replace("?", "").split())
            if not remainder_words & _TASK_KEYWORDS:
                return True
    return False


# ──────────────────────────────────────────────
#  Graph Nodes
# ──────────────────────────────────────────────

def generator_node(state: AgentState) -> Dict[str, Any]:
    """Generator Agent: writes/fixes code based on task and feedback."""
    messages = state["messages"]
    feedback = state.get("feedback")
    iterations = state.get("iterations", 0)

    # Find last user message for smart routing
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    # Conversational shortcut — no tools, saves ~2000 tokens
    if _is_conversational(last_user_msg) and not feedback and iterations == 0:
        model = get_model()
        response = model.invoke([SystemMessage(content=CHAT_PROMPT)] + messages)
        return {"messages": [response], "iterations": iterations + 1}

    # Full coding path
    model = get_model()
    model = model.bind_tools(GENERATOR_TOOLS)
    prompt = [SystemMessage(content=GENERATOR_PROMPT)] + messages
    if feedback:
        prompt.append(HumanMessage(content=f"Execution feedback:\n{feedback}\n\nFix the code."))
    response = model.invoke(prompt)
    return {"messages": [response], "iterations": iterations + 1}


def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executor Agent: runs code and provides feedback."""
    messages = state["messages"]
    model = get_model()
    model = model.bind_tools(EXECUTOR_TOOLS)
    response = model.invoke([SystemMessage(content=EXECUTOR_PROMPT)] + messages)

    execution_result = response.content
    success = "SUCCESS" in str(execution_result) or "✅" in str(execution_result)
    return {
        "messages": [response],
        "feedback": str(execution_result),
        "execution_result": str(execution_result),
        "success": success,
    }


# ──────────────────────────────────────────────
#  Graph Construction
# ──────────────────────────────────────────────

def create_graph():
    """Build the Generator → Executor loop with tool routing."""
    workflow = StateGraph(AgentState)

    workflow.add_node("generator", generator_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("generator_tools", ToolNode(GENERATOR_TOOLS))
    workflow.add_node("executor_tools", ToolNode(EXECUTOR_TOOLS))

    workflow.set_entry_point("generator")

    # Generator routing
    def route_generator(state):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "generator_tools"
        if "READY_FOR_EXECUTION" in str(last.content):
            return "executor"
        if state.get("iterations", 0) >= state.get("max_iterations", 10):
            return END
        return END

    workflow.add_conditional_edges("generator", route_generator, {
        "generator_tools": "generator_tools",
        "executor": "executor",
        END: END,
    })
    workflow.add_edge("generator_tools", "generator")

    # Executor routing
    def route_executor(state):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "executor_tools"
        if state.get("success"):
            return END
        if state.get("iterations", 0) >= state.get("max_iterations", 10):
            return END
        return "generator"

    workflow.add_conditional_edges("executor", route_executor, {
        "executor_tools": "executor_tools",
        "generator": "generator",
        END: END,
    })
    workflow.add_edge("executor_tools", "executor")

    return workflow.compile()
