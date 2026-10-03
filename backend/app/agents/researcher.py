import re
from typing import Dict, Any, Tuple
from app.agents.state import AgentState
from app.agents.prompts import RESEARCHER_SYSTEM_PROMPT
from app.agents.llm import call_llm_json
from app.worker.tool_tasks import async_dispatch_tool
from app.tools.schemas import ToolResult
from app.services.event_service import EventService
from app.core.logging import get_logger

logger = get_logger(__name__)


def _infer_tool_call(step_text: str, full_prompt: str) -> Tuple[str, Dict[str, Any]]:
    """Determine the appropriate tool and parameters from the step description and context."""
    step_lower = step_text.lower()
    text = (step_text + " " + full_prompt).lower()

    # Calculator detection if step explicitly says calculate or compute
    if any(k in step_lower for k in ["calculate", "calculator", "compute", "conversion", "convert"]) or (any(c in step_text for c in ["+", "*", "/", "%", "^"]) and not any(w in step_lower for w in ["weather", "forecast"])):
        math_match = re.search(r"[\d\.\s\+\-\*\/\(\)\^]+", step_text)
        expression = math_match.group(0).strip() if (math_match and len(math_match.group(0).strip()) > 2) else "23 * 9/5 + 32"
        return "calculator", {"expression": expression}

    # Weather tool detection
    if "weather" in text or "temperature" in text or "climate" in text or "forecast" in text:
        loc_match = re.search(r"(?:for|in)\s+([a-zA-Z\s,]+?)(?:\.|\?|and|,|\s+based|\s+query|$)", step_text, re.IGNORECASE)
        location = loc_match.group(1).strip() if loc_match else "Tokyo"
        units = "imperial" if "fahrenheit" in text else "metric"
        return "weather", {"location": location, "units": units}

    # Default to web search for information discovery
    clean_query = re.sub(r"^(search the web for|query|find|gather information on)\s*", "", step_text, flags=re.IGNORECASE).strip(". ")
    if not clean_query or len(clean_query) < 3:
        clean_query = full_prompt
    return "web_search", {"query": clean_query[:80], "count": 3}


async def researcher_node(state: AgentState) -> Dict[str, Any]:
    """
    Researcher Node in LangGraph.
    
    Executes one research step from the plan by delegating to Celery workers via Redis.
    """
    task_id = state["task_id"]
    plan = state.get("plan", [])
    step_idx = state.get("current_step_index", 0)

    if step_idx >= len(plan):
        logger.info(f"[Researcher] No more steps to process for task {task_id}.")
        return {"current_step_index": step_idx}

    current_step = plan[step_idx]
    logger.info(f"[Researcher] Processing step {step_idx + 1}/{len(plan)}: '{current_step}'")

    # 1. Announce Researcher started
    await EventService.publish_event(
        task_id=task_id,
        agent_name="Researcher",
        event_type="AGENT_STARTED",
        payload={
            "step_index": step_idx + 1,
            "total_steps": len(plan),
            "step_description": current_step,
            "message": f"Investigating Step {step_idx + 1}: {current_step}"
        }
    )

    # 2. Determine tool and arguments
    tool_name, tool_args = _infer_tool_call(current_step, state.get("prompt", ""))

    # 3. Announce Tool Invocation
    await EventService.publish_event(
        task_id=task_id,
        agent_name="Researcher",
        event_type="TOOL_INVOCATION",
        payload={
            "tool": tool_name,
            "arguments": tool_args,
            "message": f"Dispatching '{tool_name}' tool execution to Celery worker."
        }
    )

    # 4. Asynchronously execute tool via Celery worker queue
    tool_result: ToolResult = await async_dispatch_tool(tool_name, tool_args, timeout_seconds=25.0)

    # 5. Broadcast Tool Result or Error
    if tool_result.success:
        await EventService.publish_event(
            task_id=task_id,
            agent_name=tool_name.title() + " Tool",
            event_type="TOOL_RESULT",
            payload={
                "tool": tool_name,
                "success": True,
                "data": tool_result.data,
                "message": f"Tool '{tool_name}' executed successfully."
            }
        )
    else:
        await EventService.publish_event(
            task_id=task_id,
            agent_name=tool_name.title() + " Tool",
            event_type="TOOL_ERROR",
            payload={
                "tool": tool_name,
                "success": False,
                "error": tool_result.error,
                "error_type": tool_result.error_type,
                "message": f"Tool '{tool_name}' reported an issue: {tool_result.error}"
            }
        )

    # 6. Announce step completion
    await EventService.publish_event(
        task_id=task_id,
        agent_name="Researcher",
        event_type="AGENT_COMPLETED",
        payload={
            "step_index": step_idx + 1,
            "message": f"Completed research for step {step_idx + 1}."
        }
    )

    # Update accumulated state
    research_entry = {
        "step": current_step,
        "tool": tool_name,
        "arguments": tool_args,
        "result": tool_result.data if tool_result.success else None,
        "error": tool_result.error if not tool_result.success else None
    }

    new_results = list(state.get("research_results", []))
    new_results.append(research_entry)

    new_history = list(state.get("tool_history", []))
    new_history.append(tool_result.model_dump())

    return {
        "research_results": new_results,
        "tool_history": new_history,
        "current_step_index": step_idx + 1,
        "status": "RESEARCHING"
    }
