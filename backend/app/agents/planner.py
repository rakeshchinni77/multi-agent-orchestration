import re
from typing import List, Dict, Any
from app.agents.state import AgentState
from app.agents.prompts import PLANNER_SYSTEM_PROMPT
from app.agents.llm import call_llm_json
from app.services.event_service import EventService
from app.core.logging import get_logger

logger = get_logger(__name__)


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner Node in LangGraph.
    
    Decomposes the user query into ordered, tool-ready execution steps.
    """
    task_id = state["task_id"]
    prompt = state["prompt"]

    logger.info(f"[Planner] Formulating plan for task {task_id}: '{prompt[:60]}...'")

    # 1. Announce Planner started
    await EventService.publish_event(
        task_id=task_id,
        agent_name="Planner",
        event_type="AGENT_STARTED",
        payload={
            "message": "Analyzing prompt requirements and breaking down execution plan...",
            "prompt": prompt
        }
    )

    # 2. Try LLM planning
    llm_plan = await call_llm_json(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=f"User Objective:\n{prompt}"
    )

    plan_steps: List[str] = []
    if isinstance(llm_plan, list) and len(llm_plan) > 0:
        plan_steps = [str(s) for s in llm_plan]
    elif isinstance(llm_plan, dict) and "steps" in llm_plan:
        plan_steps = [str(s) for s in llm_plan["steps"]]

    # Fallback heuristic decomposition if LLM unavailable
    if not plan_steps:
        lower = prompt.lower()
        if "weather" in lower or "temperature" in lower or "climate" in lower:
            # Extract possible location
            match = re.search(r"in\s+([a-zA-Z\s,]+)", prompt, re.IGNORECASE)
            loc = match.group(1).split("and")[0].strip() if match else "Tokyo"
            plan_steps.append(f"Query real-time weather conditions for {loc}.")
            if "convert" in lower or "celsius" in lower or "fahrenheit" in lower or "calculate" in lower or "*" in lower or "+" in lower:
                plan_steps.append("Calculate temperature conversion and numerical figures.")
            plan_steps.append(f"Synthesize comprehensive travel and packing recommendations for {loc}.")
        elif "search" in lower or "news" in lower or "latest" in lower or "electric" in lower:
            plan_steps.append(f"Search the web for up-to-date facts regarding: {prompt}.")
            plan_steps.append("Synthesize key findings and industry trends into an executive brief.")
        elif any(c in prompt for c in ["+", "-", "*", "/", "^"]):
            plan_steps.append(f"Execute mathematical calculation for expression: {prompt}.")
            plan_steps.append("Synthesize numerical analysis and verify results.")
        else:
            plan_steps.append(f"Gather research data and relevant facts for: {prompt}.")
            plan_steps.append("Synthesize findings and provide actionable solution.")

    # 3. Announce plan created
    await EventService.publish_event(
        task_id=task_id,
        agent_name="Planner",
        event_type="PLAN_CREATED",
        payload={
            "message": f"Execution plan established with {len(plan_steps)} steps.",
            "steps": plan_steps
        }
    )

    return {
        "plan": plan_steps,
        "current_step_index": 0,
        "status": "PLANNING_COMPLETED",
        "messages": state.get("messages", []) + [
            {"role": "planner", "content": f"Formulated {len(plan_steps)} steps."}
        ]
    }
