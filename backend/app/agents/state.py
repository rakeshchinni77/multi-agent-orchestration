from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    Shared state machine context passed across all LangGraph nodes.
    
    Contains the full task context, intermediate plans, tool results,
    step index counters, and synthesized outputs.
    """
    task_id: str
    prompt: str
    plan: List[str]
    current_step_index: int
    research_results: List[Dict[str, Any]]
    tool_history: List[Dict[str, Any]]
    messages: List[Dict[str, str]]
    final_result: Optional[str]
    status: str
    error: Optional[str]
