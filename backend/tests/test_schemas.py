"""
Unit tests for AI schema models defined in src/schemas/ai_schemas.py.

These tests verify:
- Each Pydantic model accepts valid data and rejects invalid data
- The Counterargument model introduced for the improved strategy prompt is correct
- The StrategyResult schema matches the structured counterarguments output format
- QAResult enforces that risk_level, warnings, gaps, and notes are all present
- DraftingResult accepts any non-empty markdown string

They do NOT call the LLM — they test the contract between the prompt output
format and the Pydantic models that parse it.
"""

import pytest
from pydantic import ValidationError

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

# ── Entity ────────────────────────────────────────────────────────────────────


def test_entity_accepts_all_improved_types():
    """The improved extraction prompt uses an expanded type vocabulary."""
    for entity_type in [
        "person",
        "company",
        "government_body",
        "place",
        "document",
        "court",
        "contract",
        "statute",
    ]:
        e = Entity(name="Test", type=entity_type, role="test role")
        assert e.type == entity_type


def test_entity_requires_name():
    with pytest.raises(ValidationError):
        Entity(type="person", role="buyer")  # type: ignore[call-arg]


def test_entity_requires_type():
    with pytest.raises(ValidationError):
        Entity(name="John", role="buyer")  # type: ignore[call-arg]


def test_entity_requires_role():
    with pytest.raises(ValidationError):
        Entity(name="John", type="person")  # type: ignore[call-arg]


# ── TimelineEvent ─────────────────────────────────────────────────────────────


def test_timeline_event_accepts_iso_date():
    t = TimelineEvent(date="2023-03-15", event="Contract signed")
    assert t.date == "2023-03-15"


def test_timeline_event_accepts_unknown_date():
    """The improved extraction prompt may emit 'unknown' for undated critical events."""
    t = TimelineEvent(date="unknown", event="Dispute arose")
    assert t.date == "unknown"


def test_timeline_event_requires_both_fields():
    with pytest.raises(ValidationError):
        TimelineEvent(date="2023-03-15")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        TimelineEvent(event="Something happened")  # type: ignore[call-arg]


# ── ExtractionResult ─────────────────────────────────────────────────────────


def test_extraction_result_valid():
    r = ExtractionResult(
        core_facts=["Fact one", "Fact two"],
        entities=[Entity(name="Alice", type="person", role="claimant")],
        chronological_timeline=[TimelineEvent(date="2023-01-01", event="Filing")],
    )
    assert len(r.core_facts) == 2


def test_extraction_result_empty_lists_are_valid():
    """The model should accept empty lists — the prompt enforces minimum content."""
    r = ExtractionResult(core_facts=[], entities=[], chronological_timeline=[])
    assert r.core_facts == []


def test_extraction_result_requires_all_three_fields():
    with pytest.raises(ValidationError):
        ExtractionResult(core_facts=["fact"])  # type: ignore[call-arg]


# ── LegalArgument ─────────────────────────────────────────────────────────────


def test_legal_argument_valid():
    a = LegalArgument(
        issue="Whether the contract is valid",
        applicable_kenyan_law="Law of Contract Act, Cap 23 — Section 3(3)",
        argument_summary="The written agreement satisfies the formal requirements.",
    )
    assert a.issue.startswith("Whether")


def test_legal_argument_requires_all_fields():
    with pytest.raises(ValidationError):
        LegalArgument(issue="issue", applicable_kenyan_law="law")  # type: ignore[call-arg]


# ── Counterargument ───────────────────────────────────────────────────────────


def test_counterargument_valid():
    """New model introduced by the improved strategy prompt."""
    c = Counterargument(
        rebutting_argument="Validity of contract",
        counterargument="Respondent may claim the contract lacks essential terms.",
    )
    assert c.rebutting_argument == "Validity of contract"
    assert "essential terms" in c.counterargument


def test_counterargument_requires_both_fields():
    with pytest.raises(ValidationError):
        Counterargument(rebutting_argument="Validity")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Counterargument(counterargument="Some rebuttal")  # type: ignore[call-arg]


def test_counterargument_fields_must_be_strings():
    with pytest.raises(ValidationError):
        Counterargument(rebutting_argument=123, counterargument="text")  # type: ignore[arg-type]


# ── StrategyResult ────────────────────────────────────────────────────────────


def test_strategy_result_valid_with_structured_counterarguments():
    r = StrategyResult(
        legal_issues=["Whether the contract is enforceable"],
        applicable_laws=["Law of Contract Act, Cap 23 — Section 3(3)"],
        arguments=[
            LegalArgument(
                issue="Enforceability",
                applicable_kenyan_law="Law of Contract Act, Cap 23",
                argument_summary="The contract meets all formal requirements.",
            )
        ],
        counterarguments=[
            Counterargument(
                rebutting_argument="Enforceability",
                counterargument="Respondent claims the contract lacks consideration.",
            )
        ],
        legal_reasoning="The facts, on balance, favour the applicant.",
    )
    assert len(r.counterarguments) == 1
    assert r.counterarguments[0].rebutting_argument == "Enforceability"


def test_strategy_result_counterarguments_must_be_counterargument_objects():
    """Plain strings are no longer valid for counterarguments after the schema change."""
    with pytest.raises(ValidationError):
        StrategyResult(
            legal_issues=["issue"],
            applicable_laws=["law"],
            arguments=[],
            counterarguments=["plain string counterargument"],  # old format — must fail
            legal_reasoning="reasoning",
        )


def test_strategy_result_serialises_counterarguments_as_dicts():
    """model_dump() must produce dicts, matching the JSON the LLM will return."""
    r = StrategyResult(
        legal_issues=[],
        applicable_laws=[],
        arguments=[],
        counterarguments=[
            Counterargument(
                rebutting_argument="Issue A",
                counterargument="Opposition will argue X.",
            )
        ],
        legal_reasoning="reasoning",
    )
    dumped = r.model_dump()
    assert isinstance(dumped["counterarguments"][0], dict)
    assert "rebutting_argument" in dumped["counterarguments"][0]
    assert "counterargument" in dumped["counterarguments"][0]


def test_strategy_result_requires_all_fields():
    with pytest.raises(ValidationError):
        StrategyResult(legal_issues=["issue"])  # type: ignore[call-arg]


# ── DraftingResult ────────────────────────────────────────────────────────────


def test_drafting_result_accepts_any_nonempty_markdown():
    brief = (
        "# IN THE MATTER OF\n"
        "## PARTIES\n## FACTS\n## ISSUES FOR DETERMINATION\n"
        "## LEGAL ARGUMENTS\n## RESPONDENT'S ANTICIPATED POSITION\n"
        "## CONCLUSION AND PRAYER FOR RELIEF\n"
    )
    r = DraftingResult(brief_markdown=brief)
    assert "## FACTS" in r.brief_markdown


def test_drafting_result_requires_brief_markdown():
    with pytest.raises(ValidationError):
        DraftingResult()  # type: ignore[call-arg]


def test_drafting_result_accepts_empty_string():
    """Schema does not enforce non-empty — the prompt does. Model accepts empty."""
    r = DraftingResult(brief_markdown="")
    assert r.brief_markdown == ""


# ── QAResult ──────────────────────────────────────────────────────────────────


def test_qa_result_valid_low_risk():
    r = QAResult(
        risk_level="LOW",
        hallucination_warnings=[],
        missing_logic=[],
        risk_notes=["Minor formatting issue in Section 2"],
    )
    assert r.risk_level == "LOW"


def test_qa_result_valid_high_risk():
    r = QAResult(
        risk_level="HIGH",
        hallucination_warnings=["Claim on page 3 not supported by source facts"],
        missing_logic=["Issue 2 is raised but never argued"],
        risk_notes=[],
    )
    assert r.risk_level == "HIGH"
    assert len(r.hallucination_warnings) == 1


def test_qa_result_requires_all_four_fields():
    """All four fields from the improved QA prompt schema must be present."""
    with pytest.raises(ValidationError):
        QAResult(risk_level="LOW", hallucination_warnings=[])  # type: ignore[call-arg]


def test_qa_result_all_list_fields_are_lists():
    r = QAResult(
        risk_level="MEDIUM",
        hallucination_warnings=["warning one"],
        missing_logic=["gap one", "gap two"],
        risk_notes=["note one"],
    )
    assert isinstance(r.hallucination_warnings, list)
    assert isinstance(r.missing_logic, list)
    assert isinstance(r.risk_notes, list)
