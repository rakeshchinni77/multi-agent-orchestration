import pytest
from app.tools.calculator import evaluate_calculator
from app.tools.weather import get_weather
from app.tools.web_search import search_web
from app.tools.registry import execute_tool
from app.tools.schemas import CalculatorInput, WeatherInput, WebSearchInput, ToolResult


def test_calculator_basic_arithmetic():
    res = evaluate_calculator(CalculatorInput(expression="25 * 4 + 10"))
    assert res.success is True
    assert res.data is not None
    assert res.data["result"] == 110


def test_calculator_math_functions():
    res = evaluate_calculator(CalculatorInput(expression="sqrt(144) + round(3.7)"))
    assert res.success is True
    assert res.data is not None
    assert res.data["result"] == 16.0


def test_calculator_division_by_zero():
    res = evaluate_calculator(CalculatorInput(expression="100 / 0"))
    assert res.success is False
    assert res.error_type == "MATH_ERROR"
    assert res.error is not None
    assert "zero" in res.error.lower()


def test_calculator_syntax_error():
    res = evaluate_calculator(CalculatorInput(expression="25 * + / 4"))
    assert res.success is False
    assert res.error_type == "SYNTAX_ERROR"


def test_calculator_security_sandbox():
    """Ensure eval/import/system calls are strictly blocked by the AST parser."""
    res = evaluate_calculator(CalculatorInput(expression="__import__('os').system('ls')"))
    assert res.success is False


def test_weather_execution():
    res = get_weather(WeatherInput(location="Tokyo", units="metric"))
    assert isinstance(res, ToolResult)
    # The tool must never raise an unhandled exception
    if res.success:
        assert res.data is not None
        assert "temperature" in res.data
        assert "condition" in res.data
    else:
        # Graceful error handling for invalid credentials / network
        assert res.error_type in ["AUTH_ERROR", "TIMEOUT_ERROR", "EXTERNAL_API_ERROR"]
        assert res.error is not None


def test_weather_empty_location():
    res = get_weather(WeatherInput(location="", units="metric"))
    assert res.success is False
    assert res.error_type == "VALIDATION_ERROR"


def test_web_search_execution():
    res = search_web(WebSearchInput(query="LangGraph Multi-Agent Orchestration", count=2))
    assert res.success is True
    assert res.data is not None
    assert "results" in res.data
    assert len(res.data["results"]) >= 1


def test_registry_execution():
    res = execute_tool("calculator", {"expression": "100 - 45"})
    assert res.success is True
    assert res.data is not None
    assert res.data["result"] == 55

    res_invalid = execute_tool("non_existent_tool", {})
    assert res_invalid.success is False
    assert res_invalid.error_type == "UNKNOWN_TOOL"
