from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    type: str
    role: str


class TimelineEvent(BaseModel):
    date: str
    event: str


class ExtractionResult(BaseModel):
    core_facts: list[str]
    entities: list[Entity]
    chronological_timeline: list[TimelineEvent]


class LegalArgument(BaseModel):
    issue: str
    applicable_kenyan_law: str
    argument_summary: str


class Counterargument(BaseModel):
    rebutting_argument: str
    counterargument: str


class StrategyResult(BaseModel):
    legal_issues: list[str]
    applicable_laws: list[str]
    arguments: list[LegalArgument]
    counterarguments: list[Counterargument]
    legal_reasoning: str


class DraftingResult(BaseModel):
    brief_markdown: str


class QAResult(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH
    hallucination_warnings: list[str]
    missing_logic: list[str]
    risk_notes: list[str]


class FinalBrief(BaseModel):
    case_summary: str
    legal_issues: list[str]
    arguments_for_client: list[str]
    risks: list[str]
    recommendations: list[str]
