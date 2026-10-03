import json
import re
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm():
    """Instantiate and return the configured LangChain ChatGroq LLM model if key is available."""
    api_key = settings.GROQ_API_KEY or settings.LLM_API_KEY
    if api_key and not api_key.startswith("mock_"):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=api_key,
                model_name=settings.GROQ_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT,
                max_retries=2
            )
        except Exception as e:
            logger.warning(f"Could not initialize ChatGroq: {e}. Falling back to heuristic reasoning.")
    return None


async def call_llm_json(system_prompt: str, user_prompt: str) -> Optional[Any]:
    """Execute LLM call and parse output as JSON."""
    llm = get_llm()
    if not llm:
        return None

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt + "\nYou MUST return valid raw JSON only. Do not wrap in markdown quotes."),
            HumanMessage(content=user_prompt)
        ]
        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # Clean markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        return json.loads(content)
    except Exception as e:
        logger.warning(f"LLM JSON call encountered issue: {e}")
        return None


async def call_llm_text(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Execute standard LLM text generation."""
    llm = get_llm()
    if not llm:
        return None

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = await llm.ainvoke(messages)
        return response.content.strip()
    except Exception as e:
        logger.warning(f"LLM text call encountered issue: {e}")
        return None
