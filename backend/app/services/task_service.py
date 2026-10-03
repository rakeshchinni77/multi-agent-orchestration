import asyncio
import uuid
from typing import Optional, Dict, Any, List
from app.db.session import AsyncSessionLocal
from app.db.repositories import TaskRepository, EventRepository
from app.services.event_service import EventService
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskService:
    """Service layer managing task lifecycle, orchestration dispatch, and query operations."""

    @staticmethod
    async def create_task(prompt: str) -> str:
        """Initialize a new task run in PENDING status and return the generated task_id."""
        task_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            await TaskRepository.create_task_run(
                session=session,
                prompt=prompt,
                task_id=task_id
            )

        # Publish initial TASK_CREATED event
        await EventService.publish_event(
            task_id=task_id,
            agent_name="System",
            event_type="TASK_CREATED",
            payload={
                "message": "Task created and queued for execution.",
                "prompt": prompt
            }
        )
        return task_id

    @staticmethod
    async def get_task_details(task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch task status and recorded trace events."""
        async with AsyncSessionLocal() as session:
            task = await TaskRepository.get_task_run(session, task_id)
            if not task:
                return None
            events = await EventRepository.get_task_events(session, task_id)

            data = task.to_dict()
            data["events"] = [e.to_dict() for e in events]
            return data

    @staticmethod
    async def list_recent_tasks(limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch recent task runs."""
        async with AsyncSessionLocal() as session:
            tasks = await TaskRepository.list_task_runs(session, limit=limit)
            return [t.to_dict() for t in tasks]
