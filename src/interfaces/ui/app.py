"""
AI Coding Agent — Streamlit UI
Production-grade interface with:
- Real-time execution flow panel
- Token usage dashboard
- Agent transition visibility
- Tool call + RAG chunk logging
"""

import os
import sys
import time
import streamlit as st
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv

# Ensure project root is in python path so imports like 'from src.core...' work
# Current file: src/interfaces/ui/app.py
# Root is ../../../ from here
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

load_dotenv()

from src.core.agent.graph import (
    create_graph,
    get_token_tracker,
    reset_token_tracker,
)

# ──────────────────────────────────────────────
#  Page Config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="AI Coding Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────
#  Custom CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}

/* Header */
.hero-title {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0;
    padding: 0;
}
.hero-sub {
    text-align: center;
    color: #6b7280;
    font-size: 0.95rem;
    margin-top: 0;
}

/* Stat cards */
.stat-row {
    display: flex;
    gap: 12px;
    margin: 12px 0;
}
.stat-card {
    background: linear-gradient(135deg, rgba(102,126,234,0.06) 0%, rgba(118,75,162,0.06) 100%);
    border: 1px solid rgba(102,126,234,0.15);
    border-radius: 10px;
    padding: 10px 16px;
    flex: 1;
    text-align: center;
}
.stat-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #667eea;
    font-family: 'JetBrains Mono', monospace;
}
.stat-label {
    font-size: 0.7rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Execution log */
.exec-step {
    border-left: 3px solid #667eea;
    padding: 6px 12px;
    margin: 6px 0;
    background: rgba(102,126,234,0.04);
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
}
.exec-step-tool {
    border-left-color: #f59e0b;
    background: rgba(245,158,11,0.04);
}
.exec-step-ok {
    border-left-color: #10b981;
    background: rgba(16,185,129,0.04);
}
.exec-step-err {
    border-left-color: #ef4444;
    background: rgba(239,68,68,0.04);
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Session State Defaults
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "exec_log" not in st.session_state:
    st.session_state.exec_log = []
if "token_stats" not in st.session_state:
    st.session_state.token_stats = {"input": 0, "output": 0, "total": 0, "calls": 0, "model": "—", "duration": 0}
if "running" not in st.session_state:
    st.session_state.running = False


# ──────────────────────────────────────────────
#  Lazy RAG Loader
# ──────────────────────────────────────────────

@st.cache_resource
def load_rag_system():
    """Lazily load RAG to avoid import-time pydantic crash."""
    try:
        from src.infrastructure.rag.vector_store import rag_system
        return rag_system
    except Exception as e:
        st.warning(f"RAG unavailable: {e}")
        return None


# ──────────────────────────────────────────────
#  Header
# ──────────────────────────────────────────────

st.markdown('<h1 class="hero-title">🤖 AI Coding Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Multi-agent system: Generator → Executor loop with tool orchestration</p>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Sidebar — Configuration
# ──────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuration")

    provider = st.selectbox(
        "LLM Provider",
        ["openai", "groq", "ollama", "anthropic"],
        index=0,
    )

    max_iters = st.slider("Max Iterations", 1, 20, 10)

    use_rag = st.toggle("📚 RAG Context", value=False)

    st.divider()

    # Token stats
    st.subheader("📊 Token Usage")
    stats = st.session_state.token_stats
    col1, col2 = st.columns(2)
    col1.metric("Input", f"{stats['input']:,}")
    col2.metric("Output", f"{stats['output']:,}")
    col1.metric("Total", f"{stats['total']:,}")
    col2.metric("LLM Calls", stats['calls'])
    st.caption(f"Model: `{stats['model']}`")
    st.caption(f"Duration: `{stats['duration']:.1f}s`")

    # Estimated cost
    cost = (stats['input'] * 0.15 + stats['output'] * 0.60) / 1_000_000
    st.metric("Est. Cost", f"${cost:.4f}")

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.exec_log = []
        st.session_state.token_stats = {"input": 0, "output": 0, "total": 0, "calls": 0, "model": "—", "duration": 0}
        st.rerun()


# ──────────────────────────────────────────────
#  Main Layout: Chat | Execution Log
# ──────────────────────────────────────────────

chat_col, log_col = st.columns([3, 2])

# ── Chat Column ──
with chat_col:
    st.subheader("💬 Chat")

    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ── Execution Log Column ──
with log_col:
    st.subheader("📋 Execution Flow")

    if not st.session_state.exec_log:
        st.caption("Send a message to see the agent execution flow here.")
    else:
        for entry in st.session_state.exec_log:
            css_class = entry.get("css", "exec-step")
            icon = entry.get("icon", "⚡")
            st.markdown(
                f'<div class="{css_class}"><strong>{icon} {entry["title"]}</strong><br>{entry["detail"]}</div>',
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────
#  Chat Input & Agent Execution
# ──────────────────────────────────────────────

if prompt := st.chat_input("Describe a coding task..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_col:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Reset for new run
    reset_token_tracker()
    st.session_state.exec_log = []
    start_time = time.time()

    # Apply provider
    if provider:
        os.environ["DEFAULT_LLM_PROVIDER"] = provider

    # Convert history to LangChain messages
    lc_messages = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    # RAG context
    rag_context = ""
    if use_rag:
        rag = load_rag_system()
        if rag:
            try:
                rag_docs = rag.get_context_for_query(prompt, k=2)
                if rag_docs:
                    rag_context = f"\n\nRelevant Context:\n{rag_docs}\n"
                    st.session_state.exec_log.append({
                        "title": "RAG Context Loaded",
                        "detail": f"Retrieved {len(rag_docs)} chars of context from vector store",
                        "icon": "📚",
                        "css": "exec-step",
                    })
            except Exception as e:
                st.session_state.exec_log.append({
                    "title": "RAG Error",
                    "detail": str(e),
                    "icon": "⚠️",
                    "css": "exec-step-err",
                })

    # Build final message with RAG
    final_content = prompt + rag_context
    if rag_context:
        lc_messages[-1] = HumanMessage(content=final_content)

    # Inputs
    inputs = {
        "messages": lc_messages,
        "iterations": 0,
    }
    # Handle max_iterations in state if graph supports it or pass in configurable
    # The graph usually takes config via 'configurable' or state. 
    # State has 'max_iterations'.
    inputs["max_iterations"] = max_iters

    # Log start
    st.session_state.exec_log.append({
        "title": f"Agent Run Started",
        "detail": f"Provider: {provider} | Time: {datetime.now().strftime('%H:%M:%S')}",
        "icon": "🚀",
        "css": "exec-step",
    })

    # ── Stream the graph ──
    graph = create_graph()
    bot_response = ""
    prev_msg_count = len(lc_messages)

    with chat_col:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_placeholder.markdown("⏳ Thinking...")

    with log_col:
        log_container = st.container()

    try:
        for event in graph.stream(inputs, stream_mode="values"):
            if "messages" not in event or not event["messages"]:
                continue

            all_msgs = event["messages"]
            if len(all_msgs) <= prev_msg_count:
                continue

            # Process new messages
            for msg in all_msgs[prev_msg_count:]:
                content = msg.content if hasattr(msg, "content") else str(msg)
                is_tool_call = hasattr(msg, "tool_calls") and msg.tool_calls
                is_tool_result = hasattr(msg, "type") and msg.type == "tool"
                is_ai = hasattr(msg, "type") and msg.type == "ai"

                if is_tool_call:
                    for tc in msg.tool_calls:
                        name = tc.get("name", "unknown")
                        args = str(tc.get("args", {}))
                        if len(args) > 200:
                            args = args[:200] + "..."
                        st.session_state.exec_log.append({
                            "title": f"Tool Call: {name}",
                            "detail": f"<code>{args}</code>",
                            "icon": "🔧",
                            "css": "exec-step-tool",
                        })

                elif is_tool_result:
                    tool_name = getattr(msg, "name", "unknown")
                    result_text = str(content)[:300]
                    if len(str(content)) > 300:
                        result_text += "..."
                    status = "✅" if "error" not in result_text.lower() else "⚠️"
                    st.session_state.exec_log.append({
                        "title": f"Tool Result: {tool_name}",
                        "detail": f"<code>{result_text}</code>",
                        "icon": status,
                        "css": "exec-step-ok" if status == "✅" else "exec-step-err",
                    })

                elif is_ai and content:
                    if "READY_FOR_EXECUTION" in content:
                        st.session_state.exec_log.append({
                            "title": "Generator → Executor",
                            "detail": "Code is ready. Handing off to Executor Agent.",
                            "icon": "⚡",
                            "css": "exec-step",
                        })
                    elif "SUCCESS" in content or "✅" in content:
                        st.session_state.exec_log.append({
                            "title": "Execution Successful",
                            "detail": content[:200],
                            "icon": "✅",
                            "css": "exec-step-ok",
                        })
                        bot_response = content
                    elif "Execution failed" in content or "❌" in content:
                        st.session_state.exec_log.append({
                            "title": "Execution Failed",
                            "detail": content[:200],
                            "icon": "❌",
                            "css": "exec-step-err",
                        })
                    else:
                        bot_response = content
                        st.session_state.exec_log.append({
                            "title": "Agent Response",
                            "detail": content[:150] + ("..." if len(content) > 150 else ""),
                            "icon": "💬",
                            "css": "exec-step",
                        })

            prev_msg_count = len(all_msgs)

            # Live update the response
            if bot_response:
                response_placeholder.markdown(bot_response)

            # Redraw log
            with log_container:
                for entry in st.session_state.exec_log[-5:]:
                    css_class = entry.get("css", "exec-step")
                    icon = entry.get("icon", "⚡")
                    st.markdown(
                        f'<div class="{css_class}"><strong>{icon} {entry["title"]}</strong><br>{entry["detail"]}</div>',
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        bot_response = f"❌ Error: {str(e)}"
        response_placeholder.markdown(bot_response)
        st.session_state.exec_log.append({
            "title": "Error",
            "detail": str(e),
            "icon": "❌",
            "css": "exec-step-err",
        })

    # Final stats
    elapsed = time.time() - start_time
    tracker = get_token_tracker()
    data = tracker.to_dict()
    st.session_state.token_stats = {
        "input": data["input_tokens"],
        "output": data["output_tokens"],
        "total": data["total_tokens"],
        "calls": data["llm_calls"],
        "model": data["model"] or provider,
        "duration": elapsed,
    }

    st.session_state.exec_log.append({
        "title": f"Run Completed in {elapsed:.1f}s",
        "detail": f"Tokens: {data['total_tokens']:,} | LLM calls: {data['llm_calls']}",
        "icon": "⏱️",
        "css": "exec-step-ok",
    })

    # Save assistant message
    if bot_response:
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "(No response generated)"})

    # Rerun to redraw with final state
    st.rerun()
