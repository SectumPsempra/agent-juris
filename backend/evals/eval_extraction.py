"""Extraction agent evaluation against golden cases.

Runs the extraction agent over each golden case, validates the structured output
against the expected constraints defined in ``golden_cases.json``, and prints a
per-case pass/fail report with an aggregate score.

Usage:
    uv run python -m evals.eval_extraction

The script exits with code 1 if any case fails so it can be used as a CI gate.
"""

import asyncio
import json
import sys
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden_cases.json"


def _check(case_id: str, extraction: object, expected: dict) -> list[str]:
    """Return a list of failure messages for a single golden case.

    An empty list means the extraction passed all constraints.
    """
    failures: list[str] = []

    facts: list = getattr(extraction, "core_facts", [])
    entities: list = getattr(extraction, "entities", [])
    timeline: list = getattr(extraction, "chronological_timeline", [])

    # Minimum fact count
    min_facts = expected.get("min_core_facts", 0)
    if len(facts) < min_facts:
        failures.append(f"[{case_id}] core_facts: expected >= {min_facts}, got {len(facts)}")

    # Required entity names present
    entity_names = {e.name.lower() for e in entities}
    for name in expected.get("required_entity_names", []):
        if name.lower() not in entity_names:
            failures.append(f"[{case_id}] missing entity name: '{name}'")

    # Required entity types present
    entity_types = {e.type.lower() for e in entities}
    for etype in expected.get("required_entity_types", []):
        if etype.lower() not in entity_types:
            failures.append(f"[{case_id}] missing entity type: '{etype}'")

    # Minimum timeline events
    min_events = expected.get("min_timeline_events", 0)
    if len(timeline) < min_events:
        failures.append(
            f"[{case_id}] timeline: expected >= {min_events} events, got {len(timeline)}"
        )

    # Timeline date prefix check
    date_prefix = expected.get("timeline_must_contain_date_prefix")
    if date_prefix:
        dates = [e.date for e in timeline]
        if not any(d.startswith(date_prefix) for d in dates):
            failures.append(
                f"[{case_id}] timeline missing event with date prefix '{date_prefix}'"
                f"; found: {dates}"
            )

    # Keyword presence in facts text
    facts_blob = " ".join(facts).lower()
    for kw in expected.get("expected_keywords_in_facts", []):
        if kw.lower() not in facts_blob:
            failures.append(f"[{case_id}] core_facts missing expected keyword: '{kw}'")

    return failures


async def run_eval() -> bool:
    """Run all golden cases and return True if every case passed."""
    from src.agents.extraction import run_extraction_agent

    cases = json.loads(GOLDEN_PATH.read_text())
    total = len(cases)
    passed = 0
    all_failures: list[str] = []

    for case in cases:
        cid = case["id"]
        print(f"  Running {cid}: {case['description']} ...", end=" ", flush=True)
        try:
            extraction = await run_extraction_agent(case["case_text"])
            failures = _check(cid, extraction, case["expected"])
            if failures:
                print("FAIL")
                all_failures.extend(failures)
            else:
                print("PASS")
                passed += 1
        except Exception as exc:
            print(f"ERROR ({exc})")
            all_failures.append(f"[{cid}] agent raised exception: {exc}")

    print(f"\nResult: {passed}/{total} passed")

    if all_failures:
        print("\nFailures:")
        for f in all_failures:
            print(f"  - {f}")

    return passed == total


def main() -> None:
    print("Extraction eval — golden cases\n")
    success = asyncio.run(run_eval())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
