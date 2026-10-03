from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """Payload schema for submitting a new multi-agent workflow prompt."""
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="The problem statement or multi-step question for the agent swarm to resolve."
    )


class TaskCreateResponse(BaseModel):
    """Immediate response returning unique task identifier."""
    task_id: str = Field(..., description="Unique UUIDv4 identifier of the created task.")
    status: str = Field(default="PENDING", description="Initial task lifecycle status.")
    message: str = Field(default="Task submitted and workflow initiated asynchronously.")


class AgentEventSchema(BaseModel):
    id: str
    task_run_id: str
    agent_name: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None


class TaskDetailResponse(BaseModel):
    id: str
    prompt: str
    status: str
    final_result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    events: List[AgentEventSchema] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
