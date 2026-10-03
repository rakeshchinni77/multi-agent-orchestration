import time
from app.worker.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.worker.tasks.ping_task")
def ping_task(message: str = "pong") -> dict:
    """Diagnostic task for verifying Celery worker health and broker connectivity."""
    logger.info(f"Ping task received with message: {message}")
    return {
        "status": "ok",
        "message": message,
        "timestamp": time.time()
    }
