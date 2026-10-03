import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import TaskRun, AgentEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskRepository:
    """Repository handling persistence operations for TaskRun records."""

    @staticmethod
    async def create_task_run(
        session: AsyncSession,
        prompt: str,
        task_id: Optional[str] = None
    ) -> TaskRun:
        task_id = task_id or str(uuid.uuid4())
        task_run = TaskRun(
            id=task_id,
            prompt=prompt,
            status="PENDING",
            created_at=datetime.utcnow()
        )
        session.add(task_run)
        await session.commit()
        await session.refresh(task_run)
        logger.info(f"Created TaskRun record: id={task_id}, status=PENDING")
        return task_run

    @staticmethod
    async def get_task_run(
        session: AsyncSession,
        task_id: str
    ) -> Optional[TaskRun]:
        stmt = select(TaskRun).where(TaskRun.id == task_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_task_status(
        session: AsyncSession,
        task_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[TaskRun]:
        task = await TaskRepository.get_task_run(session, task_id)
        if not task:
            logger.warning(f"TaskRun {task_id} not found for status update to {status}")
            return None

        task.status = status
        if status == "RUNNING" and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ["COMPLETED", "FAILED"]:
            task.completed_at = datetime.utcnow()

        if error_message:
            task.error_message = error_message

        await session.commit()
        await session.refresh(task)
        logger.info(f"Updated TaskRun {task_id} status={status}")
        return task

    @staticmethod
    async def save_final_result(
        session: AsyncSession,
        task_id: str,
        final_result: str
    ) -> Optional[TaskRun]:
        task = await TaskRepository.get_task_run(session, task_id)
        if not task:
            return None

        task.final_result = final_result
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()

        await session.commit()
        await session.refresh(task)
        logger.info(f"Saved final result for TaskRun {task_id}")
        return task

    @staticmethod
    async def list_task_runs(
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0
    ) -> List[TaskRun]:
        stmt = (
            select(TaskRun)
            .order_by(TaskRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


class EventRepository:
    """Repository handling persistence operations for granular AgentEvent audit logs."""

    @staticmethod
    async def save_agent_event(
        session: AsyncSession,
        task_run_id: str,
        agent_name: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> AgentEvent:
        event = AgentEvent(
            id=str(uuid.uuid4()),
            task_run_id=task_run_id,
            agent_name=agent_name,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.utcnow()
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @staticmethod
    async def get_task_events(
        session: AsyncSession,
        task_run_id: str
    ) -> List[AgentEvent]:
        stmt = (
            select(AgentEvent)
            .where(AgentEvent.task_run_id == task_run_id)
            .order_by(AgentEvent.timestamp.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
