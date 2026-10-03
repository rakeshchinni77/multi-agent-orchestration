from typing import Dict, Any, Callable, Type
from pydantic import BaseModel, ValidationError
from app.tools.schemas import WebSearchInput, WeatherInput, CalculatorInput, ToolResult
from app.tools.web_search import search_web
from app.tools.weather import get_weather
from app.tools.calculator import evaluate_calculator
from app.core.logging import get_logger

logger = get_logger(__name__)

# Tool specification registry mapping
TOOL_DEFINITIONS = {
    "web_search": {
        "name": "web_search",
        "description": "Search the live web for recent events, facts, articles, and general information.",
        "schema": WebSearchInput,
        "func": search_web,
    },
    "weather": {
        "name": "weather",
        "description": "Get current weather conditions (temperature, condition, humidity, wind) for any city globally.",
        "schema": WeatherInput,
        "func": get_weather,
    },
    "calculator": {
        "name": "calculator",
        "description": "Safely compute mathematical calculations and expressions (e.g. unit conversions, arithmetic, powers).",
        "schema": CalculatorInput,
        "func": evaluate_calculator,
    },
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
    """
    Validate input parameters against the tool's Pydantic schema and execute it safely.
    
    Returns a structured ToolResult with status, data, and error information.
    """
    tool_meta = TOOL_DEFINITIONS.get(tool_name.lower())
    if not tool_meta:
        logger.error(f"Attempted execution of unknown tool: '{tool_name}'")
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=f"Tool '{tool_name}' is not recognized in the tool registry. Available tools: {list(TOOL_DEFINITIONS.keys())}",
            error_type="UNKNOWN_TOOL",
            retryable=False
        )

    schema_cls: Type[BaseModel] = tool_meta["schema"]
    func: Callable = tool_meta["func"]

    # 1. Pydantic validation
    try:
        validated_input = schema_cls(**arguments)
    except ValidationError as ve:
        logger.warning(f"Parameter validation failed for tool '{tool_name}': {ve}")
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=f"Invalid arguments for {tool_name}: {str(ve)}",
            error_type="VALIDATION_ERROR",
            retryable=False
        )

    # 2. Tool execution with safety boundary
    try:
        result: ToolResult = func(validated_input)
        return result
    except Exception as e:
        logger.error(f"Unhandled exception during execution of '{tool_name}': {e}", exc_info=True)
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=f"Internal error executing {tool_name}: {str(e)}",
            error_type="EXECUTION_ERROR",
            retryable=False
        )


def get_available_tools_metadata():
    """Return JSON schemas of registered tools for LLM function calling prompts."""
    tools_list = []
    for name, meta in TOOL_DEFINITIONS.items():
        tools_list.append({
            "name": name,
            "description": meta["description"],
            "parameters": meta["schema"].model_json_schema()
        })
    return tools_list
