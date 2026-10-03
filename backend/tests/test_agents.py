import pytest
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.synthesizer import synthesizer_node
from app.agents.router import route_next_step


@pytest.mark.asyncio
async def test_planner_node():
    state: AgentState = {
        "task_id": "test-task-1",
        "prompt": "What is the weather in Tokyo?",
        "plan": [],
        "current_step_index": 0,
        "research_results": [],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "INITIALIZED",
        "error": None
    }
    result = await planner_node(state)
    assert len(result["plan"]) > 0
    assert result["current_step_index"] == 0
    assert result["status"] == "PLANNING_COMPLETED"


@pytest.mark.asyncio
async def test_researcher_node():
    state: AgentState = {
        "task_id": "test-task-2",
        "prompt": "Calculate temperature",
        "plan": ["Calculate 100 * 2.5 conversion."],
        "current_step_index": 0,
        "research_results": [],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "PLANNING_COMPLETED",
        "error": None
    }
    result = await researcher_node(state)
    assert result["current_step_index"] == 1
    assert len(result["research_results"]) == 1
    assert result["research_results"][0]["tool"] == "calculator"


@pytest.mark.asyncio
async def test_synthesizer_node():
    state: AgentState = {
        "task_id": "test-task-3",
        "prompt": "What is the weather in Tokyo?",
        "plan": ["Query weather in Tokyo."],
        "current_step_index": 1,
        "research_results": [
            {
                "step": "Query weather in Tokyo.",
                "tool": "weather",
                "result": {"location": "Tokyo", "temperature": "21°C", "condition": "Partly Cloudy"}
            }
        ],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "RESEARCHING",
        "error": None
    }
    result = await synthesizer_node(state)
    assert result["status"] == "COMPLETED"
    assert result["final_result"] is not None
    assert "Tokyo" in result["final_result"]


def test_router_logic():
    state_continue: AgentState = {
        "task_id": "t1",
        "prompt": "test",
        "plan": ["step 1", "step 2"],
        "current_step_index": 1,
        "research_results": [],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "RESEARCHING",
        "error": None
    }
    assert route_next_step(state_continue) == "researcher"

    state_done: AgentState = {
        "task_id": "t1",
        "prompt": "test",
        "plan": ["step 1", "step 2"],
        "current_step_index": 2,
        "research_results": [],
        "tool_history": [],
        "messages": [],
        "final_result": None,
        "status": "RESEARCHING",
        "error": None
    }
    assert route_next_step(state_done) == "synthesizer"
