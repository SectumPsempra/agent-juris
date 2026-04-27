"""Quality-assurance agent.

Audits the AI-drafted brief for hallucinations, statute citation errors,
logical gaps, and internal inconsistencies before it reaches a human reviewer.
"""

import json
import time

import instructor

from src.agents.prompts import QA_PROMPT
from src.core.logging import get_logger
from src.core.openai_client import get_async_client
from src.schemas.ai_schemas import DraftingResult, ExtractionResult, QAResult

logger = get_logger(__name__)

_MODEL = "gpt-4o-mini"


async def run_qa_agent(
    extraction: ExtractionResult,
    draft: DraftingResult,
) -> QAResult:
    """Audit a drafted brief against the source facts and return a structured risk report."""
    client = instructor.from_openai(get_async_client(), mode=instructor.Mode.JSON)

    user_content = (
        f"Source facts:\n{json.dumps(extraction.core_facts, indent=2)}\n\n"
        f"Draft brief (markdown):\n{draft.brief_markdown}"
    )

    logger.info("llm_call_start", agent="qa", model=_MODEL)
    start = time.monotonic()

    result, completion = await client.chat.completions.create_with_completion(
        model=_MODEL,
        response_model=QAResult,
        messages=[
            {"role": "system", "content": QA_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    usage = completion.usage
    logger.info(
        "llm_call_complete",
        agent="qa",
        model=_MODEL,
        duration_ms=duration_ms,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )

    return result
