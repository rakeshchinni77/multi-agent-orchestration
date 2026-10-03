from datetime import datetime
from typing import Dict, Any, Optional
from app.db.session import AsyncSessionLocal
from app.db.repositories import EventRepository
from app.services.websocket_manager import ws_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventService:
    """
    Central event dispatcher coordinating:
    1. Persistent audit storage in PostgreSQL (AgentEvent table)
    2. Real-time WebSocket streaming to connected frontend clients
    """

    @staticmethod
    async def publish_event(
        task_id: str,
        agent_name: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record the event in PostgreSQL and broadcast to WebSockets.
        """
        timestamp = datetime.utcnow().isoformat()
        event_envelope = {
            "task_id": task_id,
            "agent": agent_name,
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp
        }

        # 1. Persist to PostgreSQL audit table
        try:
            async with AsyncSessionLocal() as session:
                await EventRepository.save_agent_event(
                    session=session,
                    task_run_id=task_id,
                    agent_name=agent_name,
                    event_type=event_type,
                    payload=payload
                )
        except Exception as e:
            logger.error(f"Failed to persist event to PostgreSQL for task {task_id}: {e}")

        # 2. Broadcast to connected WebSocket subscribers
        try:
            await ws_manager.broadcast_event(task_id, event_envelope)
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket event for task {task_id}: {e}")

        logger.debug(f"[Event] task={task_id[:8]} agent={agent_name} type={event_type}")
        return event_envelope
