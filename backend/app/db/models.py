import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    final_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to granular agent execution trace events
    events = relationship(
        "AgentEvent",
        back_populates="task_run",
        cascade="all, delete-orphan",
        order_by="AgentEvent.timestamp.asc()"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "status": self.status,
            "final_result": self.final_result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_run_id = Column(String(36), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    task_run = relationship("TaskRun", back_populates="events")

    __table_args__ = (
        Index("idx_task_timestamp", "task_run_id", "timestamp"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "task_run_id": self.task_run_id,
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
