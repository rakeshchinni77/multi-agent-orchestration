from typing import Optional, Any, Literal, Dict
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(
        ...,
        description="The specific search query term to look up current information on the web."
    )
    count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="The number of search results to return (between 1 and 10)."
    )


class WeatherInput(BaseModel):
    location: str = Field(
        ...,
        description="The city name and optional country code (e.g. 'Tokyo', 'London, UK', 'New York, US')."
    )
    units: Literal["metric", "imperial"] = Field(
        default="metric",
        description="Measurement units: 'metric' (Celsius, m/s) or 'imperial' (Fahrenheit, mph)."
    )


class CalculatorInput(BaseModel):
    expression: str = Field(
        ...,
        description="A mathematical expression to safely evaluate, e.g. '(23 * 9/5) + 32' or 'sqrt(144) * 5'."
    )


class ToolResult(BaseModel):
    """Standardized result envelope returned by all custom tools."""
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    retryable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
