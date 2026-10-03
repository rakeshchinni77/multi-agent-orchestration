from typing import Literal
from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def route_next_step(state: AgentState) -> Literal["researcher", "synthesizer"]:
    """
    Conditional routing edge in the LangGraph state machine.
    
    Determines whether further planned steps remain for the Researcher agent,
    or if execution should transition to the Synthesizer agent.
    """
    plan = state.get("plan", [])
    current_index = state.get("current_step_index", 0)

    logger.debug(f"[Router] Evaluating progress: step {current_index} of {len(plan)}")

    if current_index < len(plan):
        logger.info(f"[Router] Routing to Researcher for step {current_index + 1}/{len(plan)}.")
        return "researcher"

    logger.info("[Router] All planned steps fulfilled. Routing to Synthesizer.")
    return "synthesizer"
