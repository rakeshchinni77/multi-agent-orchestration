"""Custom tools with strict Pydantic schemas, AST evaluation, and external API connectors."""

from app.tools.schemas import WebSearchInput, WeatherInput, CalculatorInput, ToolResult
from app.tools.web_search import search_web
from app.tools.weather import get_weather
from app.tools.calculator import evaluate_calculator
from app.tools.registry import execute_tool, TOOL_DEFINITIONS, get_available_tools_metadata

__all__ = [
    "WebSearchInput",
    "WeatherInput",
    "CalculatorInput",
    "ToolResult",
    "search_web",
    "get_weather",
    "evaluate_calculator",
    "execute_tool",
    "TOOL_DEFINITIONS",
    "get_available_tools_metadata",
]
