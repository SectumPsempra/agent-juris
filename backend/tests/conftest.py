"""
Shared fixtures, mock data, and helpers for all test modules.

Architecture:
- Each test gets a fresh per-test SQLite file (via tmp_path) — no shared state.
- `get_db` is overridden so routes hit the test DB, not production.
- `init_db` is patched so the lifespan doesn't touch the production DB.
- All 4 agents + RAG are patched at the orchestrator level so tests run
  instantly with zero API cost. Individual tests can override side_effect
  on specific mocks to simulate failures.
"""

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import models first so they register with Base.metadata before any test creates tables.
import src.database.models as _models  # noqa: F401
from src.database.models import Base
from src.database.session import get_db
from src.main import app as fastapi_app
from src.schemas.ai_schemas import (
    Counterargument,
    DraftingResult,
    Entity,
    ExtractionResult,
    LegalArgument,
    QAResult,
    StrategyResult,
    TimelineEvent,
)

# ── Canonical mock outputs ────────────────────────────────────────────────────

MOCK_EXTRACTION = ExtractionResult(
    core_facts=[
        "John Kamau signed a written land sale agreement with Sarah Wanjiru on 15 March 2023",
        "The agreed price was KES 5,000,000 for parcel No. 123/456 in Kiambu County",
        "John paid a deposit of KES 500,000 and was given possession",
        "Sarah refuses to execute transfer documents and claims the agreement is void",
    ],
    entities=[
        Entity(name="John Kamau", type="person", role="buyer"),
        Entity(name="Sarah Wanjiru", type="person", role="seller"),
        Entity(name="Kiambu County", type="place", role="jurisdiction"),
    ],
    chronological_timeline=[
        TimelineEvent(date="15 March 2023", event="Written sale agreement signed"),
        TimelineEvent(
            date="15 March 2023", event="Deposit of KES 500,000 paid; possession granted"
        ),
        TimelineEvent(
            date="after 15 March 2023", event="Sarah refuses to execute transfer documents"
        ),
    ],
)

MOCK_STRATEGY = StrategyResult(
    legal_issues=[
        "Validity of the written land sale contract",
        "Entitlement to specific performance",
        "Claim for damages for breach of contract",
    ],
    applicable_laws=[
        "Law of Contract Act, Cap 23 — Section 3(3)",
        "Land Act, No. 6 of 2012 — Section 38",
        "Civil Procedure Act, Cap 21",
    ],
    arguments=[
        LegalArgument(
            issue="Validity of contract",
            applicable_kenyan_law="Law of Contract Act, Cap 23 — Section 3(3)",
            argument_summary="The written contract satisfies Section 3(3) of the Law of Contract Act",
        ),
        LegalArgument(
            issue="Specific performance",
            applicable_kenyan_law="Land Act, No. 6 of 2012 — Section 38",
            argument_summary="Part performance (deposit + possession) entitles John to specific performance",
        ),
    ],
    counterarguments=[
        Counterargument(
            rebutting_argument="Validity of contract",
            counterargument="Sarah may claim the contract is void for lack of essential terms",
        ),
        Counterargument(
            rebutting_argument="Specific performance",
            counterargument="Sarah may argue the deposit was conditional and possession was temporary",
        ),
    ],
    legal_reasoning=(
        "The contract is valid under Kenyan law. John's part performance strengthens "
        "his claim for specific performance under the Land Act."
    ),
)

MOCK_DRAFT = DraftingResult(
    brief_markdown=(
        "# IN THE MATTER OF John Kamau v Sarah Wanjiru\n\n"
        "## PARTIES\n"
        "The Applicant is John Kamau. The Respondent is Sarah Wanjiru.\n\n"
        "## FACTS\n"
        "On 15 March 2023, John Kamau entered into a written agreement with Sarah Wanjiru "
        "for the purchase of land parcel No. 123/456 in Kiambu County at KES 5,000,000.\n\n"
        "## ISSUES FOR DETERMINATION\n"
        "1. Whether the written agreement constitutes a valid and enforceable contract\n"
        "2. Whether John Kamau is entitled to an order of specific performance\n\n"
        "## LEGAL ARGUMENTS\n"
        "### Validity of Contract\n"
        "The agreement satisfies Section 3(3) of the Law of Contract Act, Cap 23.\n\n"
        "### Specific Performance\n"
        "Part performance entitles the Applicant to specific performance under Section 38 "
        "of the Land Act, No. 6 of 2012.\n\n"
        "## RESPONDENT'S ANTICIPATED POSITION\n"
        "The Respondent may contend the contract is void. This is untenable given the "
        "written agreement and the Applicant's part performance.\n\n"
        "## CONCLUSION AND PRAYER FOR RELIEF\n"
        "The Court should grant specific performance and award costs to the Applicant."
    )
)

MOCK_QA = QAResult(
    risk_level="LOW",
    hallucination_warnings=[],
    missing_logic=[],
    risk_notes=[],
)

# ── Shared test constants ─────────────────────────────────────────────────────

SAMPLE_CASE = (
    "On 15 March 2023, John Kamau entered into a written agreement with Sarah Wanjiru "
    "for the sale of land parcel No. 123/456 in Kiambu County for KES 5,000,000. "
    "John paid a deposit of KES 500,000 and was given possession of the land. "
    "Sarah has since refused to execute the transfer documents, claiming the agreement is void. "
    "John now seeks specific performance and damages."
)

ANALYZE_FORM_BODY = {
    "title": "John Kamau v. Sarah Wanjiru — land dispute",
    "case_text": SAMPLE_CASE,
}

USER_A = "user-alice-001"
USER_B = "user-bob-002"
HEADERS_A = {"x-user-id": USER_A}
HEADERS_B = {"x-user-id": USER_B}

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(tmp_path) -> AsyncGenerator[AsyncClient, None]:
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db():
        async with SessionLocal() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    with patch("src.main.init_db", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def mock_agents():
    """
    Patches all 4 agents and rag_retrieve at the orchestrator import level.

    Tests that simulate a specific agent failing can do:
        mock_agents["extraction"].side_effect = RuntimeError("boom")
    """
    with (
        patch(
            "src.agents.orchestrator.run_extraction_agent",
            new_callable=AsyncMock,
        ) as m_ext,
        patch(
            "src.agents.orchestrator.run_strategy_agent",
            new_callable=AsyncMock,
        ) as m_strat,
        patch(
            "src.agents.orchestrator.run_drafting_agent",
            new_callable=AsyncMock,
        ) as m_draft,
        patch(
            "src.agents.orchestrator.run_qa_agent",
            new_callable=AsyncMock,
        ) as m_qa,
        patch(
            "src.agents.orchestrator.rag_retrieve",
            new_callable=AsyncMock,
        ) as m_rag,
    ):
        m_ext.return_value = MOCK_EXTRACTION
        m_strat.return_value = MOCK_STRATEGY
        m_draft.return_value = MOCK_DRAFT
        m_qa.return_value = MOCK_QA
        m_rag.return_value = []
        yield {
            "extraction": m_ext,
            "strategy": m_strat,
            "drafting": m_draft,
            "qa": m_qa,
            "rag": m_rag,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────


async def collect_sse(response) -> list[dict]:
    """Read an SSE response stream and return all data: payloads as dicts."""
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:") :].strip()))
    return events


async def run_analyze(client: AsyncClient, headers: dict = HEADERS_A) -> str:
    """Run the full pipeline and return the case_id from the final complete event."""
    async with client.stream(
        "POST",
        "/api/v1/analyze",
        data=ANALYZE_FORM_BODY,
        headers=headers,
    ) as resp:
        events = await collect_sse(resp)
    last = events[-1]
    assert last.get("type") == "complete", last
    return last["case_id"]
