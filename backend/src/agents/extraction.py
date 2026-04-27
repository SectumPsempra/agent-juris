"""Extraction agent.

Pulls legally significant facts, named entities, and a chronological timeline
from raw case text using a structured output call via instructor.
"""

import time
from typing import Any, cast

import instructor

from src.agents.prompts import (
    EXTRACTION_PROMPT,
    EXTRACTION_PROMPT_VERSION,
    FEW_SHOT_ASSISTANT,
    FEW_SHOT_USER,
)
from src.core.logging import get_logger
from src.core.openai_client import get_async_client
from src.schemas.ai_schemas import ExtractionResult

logger = get_logger(__name__)

_MODEL = "gpt-4o-mini"


async def run_extraction_agent(case_text: str) -> ExtractionResult:
    """Extract structured legal facts from raw case text.

    Uses instructor in JSON mode so the Pydantic schema is injected into the
    prompt automatically and malformed outputs are retried transparently.
    """
    client = instructor.from_openai(get_async_client(), mode=instructor.Mode.JSON)

    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {
            "role": "user",
            "content": f"Extract structured information from this case:\n\n{case_text}",
        },
    ]

    logger.info(
        "llm_call_start",
        agent="extraction",
        model=_MODEL,
        prompt_version=EXTRACTION_PROMPT_VERSION,
    )
    start = time.monotonic()

    result, completion = await client.chat.completions.create_with_completion(
        model=_MODEL,
        response_model=ExtractionResult,
        messages=cast(Any, messages),
        temperature=0.1,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    usage = completion.usage
    logger.info(
        "llm_call_complete",
        agent="extraction",
        model=_MODEL,
        duration_ms=duration_ms,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )

    return result
