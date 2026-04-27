"""LLM-as-judge evaluation for the full analysis pipeline.

Runs the complete pipeline on each golden case, then passes the drafted brief
to a second GPT-4o call that scores it on three rubric dimensions:

  - completeness   (1-5): does the brief address all identified legal issues?
  - factual_ground (1-5): is every claim traceable to a source fact?
  - actionability  (1-5): does the brief give a Kenyan advocate clear next steps?

The judge produces a structured JSON score for each case.  Aggregate results
are printed and the script exits 1 if the mean composite score falls below a
configurable threshold (default 3.0/5.0).

Usage:
    uv run python -m evals.eval_llm_judge [--threshold 3.0]

Note: This script makes real OpenAI API calls and will incur token costs.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden_cases.json"

JUDGE_SYSTEM_PROMPT = """You are an independent evaluator assessing the quality of AI-generated
Kenyan litigation briefs.

You will receive:
1. The source case description provided to the AI.
2. The AI-generated litigation brief.

Score the brief on each dimension from 1 (very poor) to 5 (excellent):

- completeness: Does the brief address all material legal issues raised by the case facts?
  1 = major issues entirely absent; 5 = all issues identified and addressed.

- factual_ground: Is every factual claim in the brief traceable to the source case description?
  1 = multiple fabricated facts; 5 = every claim is grounded in the source material.

- actionability: Does the brief give a Kenyan advocate clear, specific next steps and relief sought?
  1 = vague and generic; 5 = specific prayer for relief, statutes cited, strategy clear.

Return ONLY valid JSON:
{
  "completeness": <int 1-5>,
  "factual_ground": <int 1-5>,
  "actionability": <int 1-5>,
  "brief_comments": "<one sentence overall observation>"
}"""


async def _judge_brief(case_text: str, brief_markdown: str) -> dict:
    """Ask GPT-4o to score a generated brief and return the structured result."""
    from openai import AsyncOpenAI

    from src.core.config import settings

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (f"Source case:\n{case_text}\n\nAI-generated brief:\n{brief_markdown}"),
            },
        ],
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content or "{}")


async def run_eval(threshold: float) -> bool:
    """Run judge evaluation on all golden cases. Returns True if threshold met."""
    from src.agents.drafting import run_drafting_agent
    from src.agents.extraction import run_extraction_agent
    from src.agents.strategy import run_strategy_agent

    cases = json.loads(GOLDEN_PATH.read_text())
    total = len(cases)
    composite_scores: list[float] = []

    for case in cases:
        cid = case["id"]
        print(f"\n  [{cid}] {case['description']}")
        try:
            extraction = await run_extraction_agent(case["case_text"])
            strategy = await run_strategy_agent(extraction, [])
            draft = await run_drafting_agent(extraction, strategy)
            scores = await _judge_brief(case["case_text"], draft.brief_markdown)

            completeness = scores.get("completeness", 0)
            factual = scores.get("factual_ground", 0)
            actionability = scores.get("actionability", 0)
            composite = (completeness + factual + actionability) / 3.0
            composite_scores.append(composite)

            print(
                f"    completeness={completeness}/5  factual_ground={factual}/5  actionability={actionability}/5"
            )
            print(f"    composite={composite:.2f}/5")
            print(f"    comment: {scores.get('brief_comments', '')}")
        except Exception as exc:
            print(f"    ERROR: {exc}")

    if not composite_scores:
        print("\nNo cases completed successfully.")
        return False

    mean = sum(composite_scores) / len(composite_scores)
    print(f"\nSummary: {len(composite_scores)}/{total} cases completed")
    print(f"Mean composite score: {mean:.2f}/5.0  (threshold: {threshold}/5.0)")

    return mean >= threshold


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-as-judge pipeline evaluation")
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Minimum mean composite score to pass (default: 3.0)",
    )
    args = parser.parse_args()

    print("LLM-as-judge eval — full pipeline\n")
    success = asyncio.run(run_eval(args.threshold))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
