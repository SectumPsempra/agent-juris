"""Strategy agent.

Derives discrete legal issues, applicable Kenyan statutes, ordered arguments,
and counterarguments from the extracted case facts and RAG context.
"""

import json
import time

import instructor

from src.agents.prompts import STRATEGY_PROMPT
from src.core.logging import get_logger
from src.core.openai_client import get_async_client
from src.schemas.ai_schemas import ExtractionResult, StrategyResult

logger = get_logger(__name__)

_MODEL_ENV_KEY = "model"


def _build_user_content(extraction: ExtractionResult, rag_context: list[str]) -> str:
    context_block = "\n".join(rag_context) if rag_context else "No precedents retrieved."
    return (
        f"Core facts:\n{json.dumps(extraction.core_facts, indent=2)}\n\n"
        f"Timeline:\n{json.dumps([t.model_dump() for t in extraction.chronological_timeline], indent=2)}\n\n"
        f"Entities:\n{json.dumps([e.model_dump() for e in extraction.entities], indent=2)}\n\n"
        f"Relevant Kenyan precedents:\n{context_block}"
    )


async def run_strategy_agent(
    extraction: ExtractionResult,
    rag_context: list[str],
) -> StrategyResult:
    """Derive a legal strategy from extraction output and retrieved precedents."""
    from src.core.config import settings

    client = instructor.from_openai(get_async_client(), mode=instructor.Mode.JSON)

    logger.info("llm_call_start", agent="strategy", model=settings.model)
    start = time.monotonic()

    result, completion = await client.chat.completions.create_with_completion(
        model=settings.model,
        response_model=StrategyResult,
        messages=[
            {"role": "system", "content": STRATEGY_PROMPT},
            {"role": "user", "content": _build_user_content(extraction, rag_context)},
        ],
        temperature=0.2,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    usage = completion.usage
    logger.info(
        "llm_call_complete",
        agent="strategy",
        model=settings.model,
        duration_ms=duration_ms,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )

    return result
