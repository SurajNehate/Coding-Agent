"""Distributed tracing with Langfuse."""
import os
from typing import Optional, Dict, Any
from functools import wraps
try:
    from langfuse import Langfuse
    # Attempt to import decorators. If they fail or are missing, we handle it below.
    # Note: verify if observe is top-level or in decorators
    try:
        from langfuse.decorators import langfuse_context, observe
    except ImportError:
        from langfuse import observe
        # langfuse_context might be missing, create a dummy
        class DummyContext:
            def update_current_trace(self, **kwargs): pass
            def update_current_observation(self, **kwargs): pass
        langfuse_context = DummyContext()

except ImportError:
    Langfuse = None
    langfuse_context = None
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator



from dotenv import load_dotenv

load_dotenv()


class TracingMiddleware:
    """Manage distributed tracing with Langfuse."""
    
    def __init__(self):
        """Initialize Langfuse client."""
        self.enabled = os.getenv("LANGFUSE_PUBLIC_KEY") is not None
        
        if self.enabled and Langfuse:
            try:
                self.client = Langfuse()
            except Exception as e:
                print(f"Warning: Failed to initialize Langfuse: {e}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
        
        self.user_id = None
        self.session_id = None
    
    def set_context(self, user_id: str, session_id: str):
        """Set tracing context."""
        self.user_id = user_id
        self.session_id = session_id
        
        if self.enabled:
            langfuse_context.update_current_trace(
                user_id=user_id,
                session_id=session_id
            )
    
    def trace_llm_call(
        self,
        model: str,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Trace an LLM call."""
        if not self.enabled:
            return
        
        langfuse_context.update_current_observation(
            name="llm_call",
            input=input_text,
            output=output_text,
            metadata={
                "model": model,
                **(metadata or {})
            }
        )
    
    def trace_tool_call(
        self,
        tool_name: str,
        input_args: Dict[str, Any],
        output: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Trace a tool execution."""
        if not self.enabled:
            return
        
        langfuse_context.update_current_observation(
            name=f"tool_{tool_name}",
            input=input_args,
            output=output,
            metadata=metadata or {}
        )
    
    def flush(self):
        """Flush pending traces."""
        if self.enabled and self.client:
            self.client.flush()


def trace_function(name: Optional[str] = None):
    """Decorator to trace function execution."""
    def decorator(func):
        @wraps(func)
        @observe(name=name or func.__name__)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Export singleton instance
tracing_middleware = TracingMiddleware()
