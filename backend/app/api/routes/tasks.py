import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.api.schemas import TaskCreateRequest, TaskCreateResponse, TaskDetailResponse
from app.services.task_service import TaskService
from app.agents.graph import execute_agent_workflow
from app.core.security import sanitize_prompt, is_valid_uuid
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a task and initiate multi-agent workflow"
)
async def submit_task(
    payload: TaskCreateRequest,
    background_tasks: BackgroundTasks
) -> TaskCreateResponse:
    """
    Primary REST endpoint to initiate tasks.
    
    1. Validates and sanitizes the user prompt.
    2. Initializes a new TaskRun record with a unique UUID in PostgreSQL.
    3. Dispatches the LangGraph multi-agent execution asynchronously to the background.
    4. Immediately returns the task_id to the client without blocking.
    """
    clean_prompt = sanitize_prompt(payload.prompt)
    if not clean_prompt or len(clean_prompt) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt must contain at least 3 valid characters."
        )

    # 1. Create task run record in DB
    task_id = await TaskService.create_task(clean_prompt)
    logger.info(f"REST POST /api/tasks: initialized task_id={task_id}")

    # 2. Dispatch workflow execution asynchronously in background
    background_tasks.add_task(execute_agent_workflow, task_id, clean_prompt)

    # 3. Return immediate response
    return TaskCreateResponse(
        task_id=task_id,
        status="PENDING",
        message="Task registered successfully; multi-agent execution running in background."
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Get task status and audit event history"
)
async def get_task_details(task_id: str) -> TaskDetailResponse:
    """Fetch status and complete event trace history for a given task ID."""
    if not is_valid_uuid(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format. Must be a standard UUID."
        )

    task_data = await TaskService.get_task_details(task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' was not found."
        )

    return TaskDetailResponse(**task_data)


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List recent task runs"
)
async def list_tasks(limit: int = 15) -> List[Dict[str, Any]]:
    """List recent task workflows for dashboard display."""
    return await TaskService.list_recent_tasks(limit=limit)
