import uuid
import pytest
from app.db.session import AsyncSessionLocal, init_db
from app.db.repositories import TaskRepository, EventRepository
from app.agents.graph import execute_agent_workflow


@pytest.mark.asyncio
async def test_full_agent_workflow_e2e():
    """Verify that an end-to-end task runs through planning, tools, and synthesis."""
    await init_db()

    prompt = "What is the weather in Tokyo and calculate 20 * 1.5?"
    task_id = str(uuid.uuid4())

    # 1. Initialize task
    async with AsyncSessionLocal() as session:
        await TaskRepository.create_task_run(session, prompt, task_id)

    # 2. Execute workflow
    await execute_agent_workflow(task_id, prompt)

    # 3. Verify task status and results in database
    async with AsyncSessionLocal() as session:
        task = await TaskRepository.get_task_run(session, task_id)
        assert task is not None
        assert task.status == "COMPLETED"
        assert task.final_result is not None
        assert len(task.final_result) > 20

        # Verify audit events logged
        events = await EventRepository.get_task_events(session, task_id)
        assert len(events) >= 3  # TASK_STARTED, PLAN_CREATED, TOOL_INVOCATION, etc.

        event_types = [e.event_type for e in events]
        assert "TASK_STARTED" in event_types
        assert "PLAN_CREATED" in event_types
        assert "FINAL_RESULT" in event_types
        assert "TASK_COMPLETED" in event_types
