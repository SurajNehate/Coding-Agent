"""Monitoring and metrics collection."""
import time
from typing import Dict, Any, Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class MetricsCollector:
    """Collect and expose Prometheus metrics."""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'agent_requests_total',
            'Total number of agent requests',
            ['user_id', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'agent_request_duration_seconds',
            'Agent request duration in seconds',
            ['user_id'],
            registry=self.registry
        )
        
        # LLM metrics
        self.llm_calls = Counter(
            'llm_calls_total',
            'Total number of LLM API calls',
            ['model', 'status'],
            registry=self.registry
        )
        
        self.llm_tokens = Counter(
            'llm_tokens_total',
            'Total number of tokens used',
            ['model', 'type'],  # type: input/output
            registry=self.registry
        )
        
        self.llm_latency = Histogram(
            'llm_latency_seconds',
            'LLM API call latency',
            ['model'],
            registry=self.registry
        )
        
        # Tool metrics
        self.tool_executions = Counter(
            'tool_executions_total',
            'Total number of tool executions',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        self.tool_duration = Histogram(
            'tool_execution_duration_seconds',
            'Tool execution duration',
            ['tool_name'],
            registry=self.registry
        )
        
        # System metrics
        self.active_sessions = Gauge(
            'active_sessions',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.error_count = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type'],
            registry=self.registry
        )
    
    def record_request(self, user_id: str, status: str, duration: float):
        """Record an agent request."""
        self.request_count.labels(user_id=user_id, status=status).inc()
        self.request_duration.labels(user_id=user_id).observe(duration)
        
        logger.info(
            "agent_request",
            user_id=user_id,
            status=status,
            duration=duration
        )
    
    def record_llm_call(
        self,
        model: str,
        status: str,
        latency: float,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """Record an LLM API call."""
        self.llm_calls.labels(model=model, status=status).inc()
        self.llm_latency.labels(model=model).observe(latency)
        
        if input_tokens > 0:
            self.llm_tokens.labels(model=model, type="input").inc(input_tokens)
        if output_tokens > 0:
            self.llm_tokens.labels(model=model, type="output").inc(output_tokens)
        
        logger.info(
            "llm_call",
            model=model,
            status=status,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
    
    def record_tool_execution(self, tool_name: str, status: str, duration: float):
        """Record a tool execution."""
        self.tool_executions.labels(tool_name=tool_name, status=status).inc()
        self.tool_duration.labels(tool_name=tool_name).observe(duration)
        
        logger.info(
            "tool_execution",
            tool_name=tool_name,
            status=status,
            duration=duration
        )
    
    def record_error(self, error_type: str, error_message: str, **context):
        """Record an error."""
        self.error_count.labels(error_type=error_type).inc()
        
        logger.error(
            "error_occurred",
            error_type=error_type,
            error_message=error_message,
            **context
        )
    
    def set_active_sessions(self, count: int):
        """Set the number of active sessions."""
        self.active_sessions.set(count)
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry)


class PerformanceMonitor:
    """Monitor performance of operations."""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.start_time = None
        self.operation_name = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if self.operation_name:
            logger.info(
                "operation_completed",
                operation=self.operation_name,
                duration=duration,
                success=exc_type is None
            )
    
    def start(self, operation_name: str):
        """Start monitoring an operation."""
        self.operation_name = operation_name
        self.start_time = time.time()
        
        logger.info(
            "operation_started",
            operation=operation_name,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def end(self, status: str = "success", **metadata):
        """End monitoring an operation."""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        
        logger.info(
            "operation_ended",
            operation=self.operation_name,
            status=status,
            duration=duration,
            **metadata
        )
        
        self.start_time = None


# Export singleton instances
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
