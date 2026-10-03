from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.synthesizer import synthesizer_node
from app.agents.router import route_next_step
from app.db.session import AsyncSessionLocal
from app.db.repositories import TaskRepository
from app.services.event_service import EventService
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_agent_graph() -> StateGraph:
    """
    Construct the stateful LangGraph execution graph connecting:
    - Planner Agent
    - Researcher Agent (with cyclic conditional routing)
    - Synthesizer Agent
    """
    graph = StateGraph(AgentState)

    # Register Nodes
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("synthesizer", synthesizer_node)

    # Set Entry Point
    graph.set_entry_point("planner")

    # Transitions
    # After Planner finishes, always transition to Researcher for the first step
    graph.add_edge("planner", "researcher")

    # From Researcher, conditionally cycle back for more steps or proceed to Synthesizer
    graph.add_conditional_edges(
        "researcher",
        route_next_step,
        {
            "researcher": "researcher",
            "synthesizer": "synthesizer"
        }
    )

    # Synthesizer is terminal node
    graph.add_edge("synthesizer", END)

    return graph


# Pre-compile the LangGraph workflow engine
agent_workflow = build_agent_graph().compile()


async def execute_agent_workflow(task_id: str, prompt: str) -> None:
    """
    Execute the compiled LangGraph state machine asynchronously for a given task.
    
    Synchronizes TaskRun status in PostgreSQL and broadcasts final status events.
    """
    logger.info(f"Starting LangGraph workflow for Task ID: {task_id}")

    # Mark task as RUNNING in database
    async with AsyncSessionLocal() as session:
        await TaskRepository.update_task_status(session, task_id, "RUNNING")

    # Broadcast TASK_STARTED
    await EventService.publish_event(
        task_id=task_id,
        agent_name="System",
        event_type="TASK_STARTED",
        payload={
            "message": "Workflow triggered and multi-agent graph initiated.",
            "task_id": task_id
        }
    )

    initial_state: AgentState = {
        "task_id": task_id,
        "prompt": prompt,
        "plan": [],
        "current_step_index": 0,
        "research_results": [],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "INITIALIZED",
        "error": None
    }

    try:
        final_state = await agent_workflow.ainvoke(initial_state)

        final_result_text = final_state.get("final_result") or "Workflow completed without generating output."

        # Persist final result in database
        async with AsyncSessionLocal() as session:
            await TaskRepository.save_final_result(session, task_id, final_result_text)

        # Broadcast TASK_COMPLETED
        await EventService.publish_event(
            task_id=task_id,
            agent_name="System",
            event_type="TASK_COMPLETED",
            payload={
                "message": "Multi-agent workflow executed successfully.",
                "final_result": final_result_text
            }
        )
        logger.info(f"LangGraph execution finished successfully for task {task_id}")

    except Exception as e:
        logger.error(f"LangGraph workflow execution failed for task {task_id}: {e}", exc_info=True)
        err_msg = str(e)

        async with AsyncSessionLocal() as session:
            await TaskRepository.update_task_status(session, task_id, "FAILED", error_message=err_msg)

        await EventService.publish_event(
            task_id=task_id,
            agent_name="System",
            event_type="TASK_FAILED",
            payload={
                "message": f"Execution halted due to error: {err_msg}",
                "error": err_msg
            }
        )
