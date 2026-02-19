from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[list[BaseMessage], operator.add]
    code: Optional[str] = None
    feedback: Optional[str] = None
    iterations: int = 0
    max_iterations: int = 5
    execution_result: Optional[str] = None
    success: bool = False
