from celery import Celery
from app.core.config import settings

# Initialize Celery application
celery_app = Celery(
    "agent_orchestrator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.worker.tasks",
        "app.worker.tool_tasks",
    ]
)

# Configure Celery parameters
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,         # Hard limit 60s
    task_soft_time_limit=45,    # Soft limit 45s
    result_expires=3600,        # Keep results for 1 hour
    worker_prefetch_multiplier=1,
)
