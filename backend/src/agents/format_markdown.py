"""Render structured agent outputs as Markdown (body only; UI supplies section title)."""

from src.schemas.ai_schemas import DraftingResult, ExtractionResult, QAResult, StrategyResult


def extraction_to_markdown(e: ExtractionResult) -> str:
    lines: list[str] = ["### Core facts", ""]
    for fact in e.core_facts:
        lines.append(f"- {fact}")
    lines.extend(["", "### Entities", ""])
    for ent in e.entities:
        lines.append(f"- **{ent.name}** — _{ent.type}_ — {ent.role}")
    lines.extend(["", "### Chronological timeline", ""])
    for ev in e.chronological_timeline:
        lines.append(f"- **{ev.date}** — {ev.event}")
    return "\n".join(lines).strip()


def rag_chunks_to_markdown(chunks: list[str]) -> str:
    if not chunks:
        return "_No precedents were retrieved for this matter._\n"
    lines: list[str] = ["### Retrieved excerpts", ""]
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"#### Source {i}")
        lines.append("")
        lines.append(chunk.strip() if chunk else "_(empty)_")
        lines.append("")
    return "\n".join(lines).strip()


def strategy_to_markdown(s: StrategyResult) -> str:
    lines: list[str] = ["### Legal issues", ""]
    for issue in s.legal_issues:
        lines.append(f"- {issue}")
    lines.extend(["", "### Applicable laws", ""])
    for law in s.applicable_laws:
        lines.append(f"- {law}")
    lines.extend(["", "### Arguments", ""])
    for arg in s.arguments:
        lines.append(f"- **{arg.issue}**  ")
        lines.append(f"  - Law: {arg.applicable_kenyan_law}")
        lines.append(f"  - Summary: {arg.argument_summary}")
        lines.append("")
    lines.extend(["### Counterarguments", ""])
    for c in s.counterarguments:
        lines.append(f"- **Re: {c.rebutting_argument}** -- {c.counterargument}")
    lines.extend(["", "### Legal reasoning", "", s.legal_reasoning.strip()])
    return "\n".join(lines).strip()


def drafting_to_markdown(d: DraftingResult) -> str:
    """Brief is already instructed to be Markdown from the model."""
    return d.brief_markdown.strip()


def qa_to_markdown(q: QAResult) -> str:
    lines: list[str] = [f"**Risk level:** `{q.risk_level}`", ""]
    lines.extend(["### Hallucination warnings", ""])
    if q.hallucination_warnings:
        lines.extend(f"- {w}" for w in q.hallucination_warnings)
    else:
        lines.append("- _None noted_")
    lines.extend(["", "### Missing logic", ""])
    if q.missing_logic:
        lines.extend(f"- {m}" for m in q.missing_logic)
    else:
        lines.append("- _None noted_")
    lines.extend(["", "### Risk notes", ""])
    if q.risk_notes:
        lines.extend(f"- {n}" for n in q.risk_notes)
    else:
        lines.append("- _None noted_")
    return "\n".join(lines).strip()
