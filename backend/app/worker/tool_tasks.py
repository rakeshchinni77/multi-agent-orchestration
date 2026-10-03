import asyncio
from typing import Dict, Any
from app.worker.celery_app import celery_app
from app.tools.registry import execute_tool
from app.tools.schemas import ToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.worker.tool_tasks.execute_tool_celery")
def execute_tool_celery(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery worker task that executes a registered custom tool off the main event loop.
    
    Prevents long I/O operations (like web scraping or HTTP requests) from blocking FastAPI.
    """
    logger.info(f"[Celery Worker] Executing tool: '{tool_name}' with args: {arguments}")
    try:
        result: ToolResult = execute_tool(tool_name, arguments)
        return result.model_dump()
    except Exception as e:
        logger.error(f"[Celery Worker] Fatal error in tool task '{tool_name}': {e}", exc_info=True)
        return {
            "tool_name": tool_name,
            "success": False,
            "error": f"Celery task worker failure: {str(e)}",
            "error_type": "CELERY_WORKER_ERROR",
            "retryable": False,
            "metadata": {}
        }


@celery_app.task(name="app.worker.tool_tasks.web_search_task")
def web_search_task(query: str, count: int = 5) -> Dict[str, Any]:
    """Dedicated Celery task wrapper for Web Search."""
    return execute_tool_celery("web_search", {"query": query, "count": count})


@celery_app.task(name="app.worker.tool_tasks.weather_task")
def weather_task(location: str, units: str = "metric") -> Dict[str, Any]:
    """Dedicated Celery task wrapper for Weather."""
    return execute_tool_celery("weather", {"location": location, "units": units})


@celery_app.task(name="app.worker.tool_tasks.calculator_task")
def calculator_task(expression: str) -> Dict[str, Any]:
    """Dedicated Celery task wrapper for Calculator."""
    return execute_tool_celery("calculator", {"expression": expression})


async def async_dispatch_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    timeout_seconds: float = 30.0
) -> ToolResult:
    """
    Dispatch a tool to Celery distributed worker queue via Redis.
    
    Polls the AsyncResult asynchronously without blocking the FastAPI event loop.
    Falls back gracefully to direct execution if Celery broker is unavailable.
    """
    logger.info(f"Dispatching tool '{tool_name}' to Celery queue...")
    try:
        # Submit task to Celery
        async_result = execute_tool_celery.delay(tool_name, arguments)

        # Non-blocking poll for completion
        start_time = asyncio.get_event_loop().time()
        while not async_result.ready():
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"Celery task {async_result.id} timed out after {timeout_seconds}s")
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"Tool execution timed out after {timeout_seconds} seconds.",
                    error_type="TASK_TIMEOUT",
                    retryable=True
                )
            await asyncio.sleep(0.2)

        data = async_result.get()
        return ToolResult(**data)

    except Exception as e:
        logger.warning(f"Celery queue dispatch failed ({e}). Falling back to local async thread execution.")
        # Graceful fallback: run locally in thread pool to prevent system blockage
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, execute_tool, tool_name, arguments)
