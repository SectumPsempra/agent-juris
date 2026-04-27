"""Drafting agent.

Produces a formally structured litigation brief in Markdown following Kenyan
High Court drafting conventions.  The output is intentionally prose/markdown
rather than JSON, so instructor is not used here; the model is prompted to
produce a specific heading structure that is then passed through as-is.
"""

import json
import time

from src.agents.prompts import DRAFTING_PROMPT
from src.core.logging import get_logger
from src.core.openai_client import get_async_client
from src.schemas.ai_schemas import DraftingResult, ExtractionResult, StrategyResult

logger = get_logger(__name__)


async def run_drafting_agent(
    extraction: ExtractionResult,
    strategy: StrategyResult,
) -> DraftingResult:
    """Draft a formal litigation brief from extracted facts and legal strategy."""
    from src.core.config import settings

    client = get_async_client()

    user_content = (
        f"Core facts:\n{json.dumps(extraction.core_facts, indent=2)}\n\n"
        f"Timeline:\n{json.dumps([t.model_dump() for t in extraction.chronological_timeline], indent=2)}\n\n"
        f"Legal strategy:\n{json.dumps(strategy.model_dump(), indent=2)}"
    )

    logger.info("llm_call_start", agent="drafting", model=settings.model)
    start = time.monotonic()

    response = await client.chat.completions.create(
        model=settings.model,
        messages=[
            {"role": "system", "content": DRAFTING_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    usage = response.usage
    logger.info(
        "llm_call_complete",
        agent="drafting",
        model=settings.model,
        duration_ms=duration_ms,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )

    brief_markdown = response.choices[0].message.content or ""
    return DraftingResult(brief_markdown=brief_markdown)
