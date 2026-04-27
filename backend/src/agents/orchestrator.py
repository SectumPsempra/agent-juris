"""Pipeline orchestrator.

Runs the five-step analysis pipeline (extraction -> RAG retrieval -> strategy
-> drafting -> QA) as a sequential async generator that yields SSE-formatted
strings.  Each step is:

  - wrapped in ``asyncio.wait_for`` to prevent a hung OpenAI call from stalling
    the stream indefinitely,
  - retried up to three times on transient OpenAI network/rate-limit errors,
  - persisted to the database as an ``AgentStep`` record,
  - emitted to the client as a ``markdown_section`` SSE event.

On any unrecoverable step failure the pipeline aborts, the ``Case`` is marked
``FAILED``, and a final ``error`` event is yielded.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from openai import APIConnectionError, APITimeoutError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.agents.drafting import run_drafting_agent
from src.agents.extraction import run_extraction_agent
from src.agents.format_markdown import (
    drafting_to_markdown,
    extraction_to_markdown,
    qa_to_markdown,
    rag_chunks_to_markdown,
    strategy_to_markdown,
)
from src.agents.qa import run_qa_agent
from src.agents.strategy import run_strategy_agent
from src.core.config import settings
from src.core.logging import get_logger
from src.database.models import AgentStep, Case
from src.rag.retriever import rag_retrieve
from src.schemas.api_schemas import AnalyzePipelineInput

logger = get_logger(__name__)

_TRANSIENT_OPENAI_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _markdown_section(section_id: str, heading: str, markdown: str) -> str:
    return _sse(
        {
            "type": "markdown_section",
            "section_id": section_id,
            "heading": heading,
            "markdown": markdown,
        }
    )


async def _run_with_retry(coro_fn, *args):
    """Execute an async callable with exponential-backoff retry on transient errors.

    Only ``RateLimitError``, ``APIConnectionError``, and ``APITimeoutError`` are
    retried (up to 3 attempts).  All other exceptions propagate immediately.
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(_TRANSIENT_OPENAI_ERRORS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    ):
        with attempt:
            return await coro_fn(*args)


async def _start_step(db: AsyncSession, case: Case, name: str, index: int) -> AgentStep:
    step = AgentStep(
        id=str(uuid.uuid4()),
        case_id=case.id,
        step_name=name,
        step_index=index,
        status="PROCESSING",
    )
    db.add(step)
    await db.commit()
    return step


async def _finish_step(db: AsyncSession, step: AgentStep, result: dict) -> None:
    step.status = "COMPLETED"
    step.result = result
    await db.commit()


async def _fail_step(db: AsyncSession, step: AgentStep) -> None:
    step.status = "FAILED"
    await db.commit()


async def run_pipeline(
    request: AnalyzePipelineInput, user_id: str, db: AsyncSession
) -> AsyncGenerator[str, None]:
    """Run the full analysis pipeline and yield SSE-formatted event strings."""
    case_id = str(uuid.uuid4())
    case = Case(
        id=case_id,
        user_id=user_id,
        title=request.title[:255],
        raw_input=request.raw_case_text,
        status="PROCESSING",
    )
    db.add(case)
    await db.commit()

    logger.info("pipeline_start", case_id=case_id, user_id=user_id, title=request.title)

    try:
        # Step 0 -- Extraction
        step = await _start_step(db, case, "extraction", 0)
        try:
            extraction = await asyncio.wait_for(
                _run_with_retry(run_extraction_agent, request.raw_case_text),
                timeout=settings.agent_step_timeout_seconds,
            )
        except Exception:
            await _fail_step(db, step)
            raise
        await _finish_step(db, step, extraction.model_dump())
        logger.info("step_complete", case_id=case_id, step="extraction")
        yield _markdown_section("extraction", "Fact extraction", extraction_to_markdown(extraction))

        # Step 1 -- RAG retrieval (non-critical: continue on failure)
        step = await _start_step(db, case, "rag_retrieval", 1)
        try:
            chunks = await asyncio.wait_for(
                rag_retrieve(request.raw_case_text),
                timeout=settings.agent_step_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("rag_retrieval_failed", case_id=case_id, reason=str(exc))
            chunks = []
            await _fail_step(db, step)
        else:
            await _finish_step(db, step, {"chunks": chunks})
            logger.info("step_complete", case_id=case_id, step="rag_retrieval", chunks=len(chunks))
        yield _markdown_section(
            "rag_retrieval",
            "Precedent retrieval",
            rag_chunks_to_markdown(chunks),
        )

        # Step 2 -- Strategy
        step = await _start_step(db, case, "strategy", 2)
        try:
            strategy = await asyncio.wait_for(
                _run_with_retry(run_strategy_agent, extraction, chunks),
                timeout=settings.agent_step_timeout_seconds,
            )
        except Exception:
            await _fail_step(db, step)
            raise
        await _finish_step(db, step, strategy.model_dump())
        logger.info("step_complete", case_id=case_id, step="strategy")
        yield _markdown_section("strategy", "Legal strategy", strategy_to_markdown(strategy))

        # Step 3 -- Drafting
        step = await _start_step(db, case, "drafting", 3)
        try:
            draft = await asyncio.wait_for(
                _run_with_retry(run_drafting_agent, extraction, strategy),
                timeout=settings.agent_step_timeout_seconds,
            )
        except Exception:
            await _fail_step(db, step)
            raise
        await _finish_step(db, step, draft.model_dump())
        logger.info("step_complete", case_id=case_id, step="drafting")
        yield _markdown_section("drafting", "Draft brief", drafting_to_markdown(draft))

        # Step 4 -- QA (non-critical: brief is still useful if QA fails)
        step = await _start_step(db, case, "qa", 4)
        try:
            qa = await asyncio.wait_for(
                _run_with_retry(run_qa_agent, extraction, draft),
                timeout=settings.agent_step_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("qa_step_failed", case_id=case_id, reason=str(exc))
            await _fail_step(db, step)
        else:
            await _finish_step(db, step, qa.model_dump())
            logger.info("step_complete", case_id=case_id, step="qa")
            yield _markdown_section("qa", "Quality review", qa_to_markdown(qa))

        case.status = "COMPLETED"
        await db.commit()
        logger.info("pipeline_complete", case_id=case_id)
        yield _sse({"type": "complete", "case_id": case_id})

    except Exception as exc:
        logger.exception("pipeline_failed", case_id=case_id, reason=str(exc))
        case.status = "FAILED"
        await db.commit()
        yield _sse({"type": "error", "detail": str(exc)})
