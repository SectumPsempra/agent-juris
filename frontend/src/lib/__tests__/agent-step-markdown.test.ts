import { describe, it, expect } from "vitest";
import { stepResultToMarkdown, STEP_HEADINGS } from "../agent-step-markdown";

// ── STEP_HEADINGS ─────────────────────────────────────────────────────────────

describe("STEP_HEADINGS", () => {
  it("has an entry for all five pipeline steps", () => {
    for (const step of [
      "extraction",
      "rag_retrieval",
      "strategy",
      "drafting",
      "qa",
    ]) {
      expect(STEP_HEADINGS[step]).toBeDefined();
    }
  });

  it("returns undefined for unknown step names", () => {
    expect(STEP_HEADINGS["unknown_step"]).toBeUndefined();
  });
});

// ── null / unknown ────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — null and unknown", () => {
  it("returns null when result is null", () => {
    expect(stepResultToMarkdown("extraction", null)).toBeNull();
  });

  it("returns null for an unrecognised step name", () => {
    expect(stepResultToMarkdown("not_a_step", { foo: "bar" })).toBeNull();
  });
});

// ── extraction ────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — extraction", () => {
  const result = {
    core_facts: [
      "John Kamau signed a land sale agreement with Sarah Wanjiru on 15 March 2023",
      "The agreed price was KES 5,000,000",
    ],
    entities: [
      { name: "John Kamau", type: "person", role: "buyer" },
      { name: "Kiambu County", type: "place", role: "jurisdiction" },
    ],
    chronological_timeline: [
      { date: "2023-03-15", event: "Written sale agreement signed" },
    ],
  };

  it("includes the Core facts heading", () => {
    expect(stepResultToMarkdown("extraction", result)).toContain(
      "### Core facts",
    );
  });

  it("renders each fact as a bullet", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("- John Kamau signed a land sale agreement");
    expect(md).toContain("- The agreed price was KES 5,000,000");
  });

  it("renders entity name, type, and role", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("John Kamau");
    expect(md).toContain("person");
    expect(md).toContain("buyer");
  });

  it("includes the Chronological timeline heading", () => {
    expect(stepResultToMarkdown("extraction", result)).toContain(
      "### Chronological timeline",
    );
  });

  it("renders timeline date and event", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("2023-03-15");
    expect(md).toContain("Written sale agreement signed");
  });

  it("handles empty core_facts gracefully", () => {
    expect(
      stepResultToMarkdown("extraction", { ...result, core_facts: [] }),
    ).toContain("### Core facts");
  });

  it("skips non-object entity entries without crashing", () => {
    const md = stepResultToMarkdown("extraction", {
      ...result,
      entities: [
        null,
        "bad",
        { name: "Valid", type: "person", role: "claimant" },
      ],
    });
    expect(md).toContain("Valid");
  });
});

// ── rag_retrieval ─────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — rag_retrieval", () => {
  it("shows 'No precedents' when chunks is empty", () => {
    expect(stepResultToMarkdown("rag_retrieval", { chunks: [] })).toContain(
      "No precedents",
    );
  });

  it("shows 'No precedents' when chunks key is missing", () => {
    expect(stepResultToMarkdown("rag_retrieval", {})).toContain(
      "No precedents",
    );
  });

  it("renders 'Retrieved excerpts' heading when chunks present", () => {
    const md = stepResultToMarkdown("rag_retrieval", {
      chunks: ["Section 3(3) of the Law of Contract Act."],
    });
    expect(md).toContain("### Retrieved excerpts");
    expect(md).toContain("Source 1");
  });

  it("numbers multiple chunks correctly", () => {
    const md = stepResultToMarkdown("rag_retrieval", {
      chunks: ["chunk a", "chunk b", "chunk c"],
    });
    expect(md).toContain("Source 1");
    expect(md).toContain("Source 2");
    expect(md).toContain("Source 3");
  });

  it("renders the chunk text content", () => {
    const text = "Section 38 of the Land Act, 2012 — specific performance.";
    expect(stepResultToMarkdown("rag_retrieval", { chunks: [text] })).toContain(
      text,
    );
  });
});

// ── strategy ──────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — strategy", () => {
  const result = {
    legal_issues: ["Whether the contract is valid"],
    applicable_laws: ["Law of Contract Act, Cap 23 — Section 3(3)"],
    arguments: [
      {
        issue: "Validity of contract",
        applicable_kenyan_law: "Law of Contract Act, Cap 23",
        argument_summary: "Written contract satisfies Section 3(3).",
      },
    ],
    counterarguments: ["Respondent may argue lack of essential terms."],
    legal_reasoning: "The contract is valid under Kenyan law.",
  };

  it("includes all five section headings", () => {
    const md = stepResultToMarkdown("strategy", result)!;
    for (const h of [
      "### Legal issues",
      "### Applicable laws",
      "### Arguments",
      "### Counterarguments",
      "### Legal reasoning",
    ]) {
      expect(md).toContain(h);
    }
  });

  it("renders argument issue, law, and summary", () => {
    const md = stepResultToMarkdown("strategy", result)!;
    expect(md).toContain("Validity of contract");
    expect(md).toContain("Law of Contract Act, Cap 23");
    expect(md).toContain("Written contract satisfies Section 3(3).");
  });

  it("renders legal reasoning text", () => {
    expect(stepResultToMarkdown("strategy", result)).toContain(
      "The contract is valid under Kenyan law.",
    );
  });

  it("handles empty arguments array without crashing", () => {
    expect(
      stepResultToMarkdown("strategy", { ...result, arguments: [] }),
    ).toContain("### Arguments");
  });
});

// ── drafting ──────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — drafting", () => {
  const brief = [
    "# IN THE MATTER OF John Kamau v Sarah Wanjiru",
    "",
    "## PARTIES",
    "The Applicant is John Kamau.",
    "",
    "## FACTS",
    "On 15 March 2023 the parties signed a sale agreement.",
    "",
    "## ISSUES FOR DETERMINATION",
    "1. Whether the agreement is enforceable",
    "",
    "## LEGAL ARGUMENTS",
    "### Validity",
    "The agreement is valid.",
    "",
    "## RESPONDENT'S ANTICIPATED POSITION",
    "Respondent contends the contract is void.",
    "",
    "## CONCLUSION AND PRAYER FOR RELIEF",
    "The Court should grant specific performance.",
  ].join("\n");

  it("returns the brief_markdown string unchanged", () => {
    expect(stepResultToMarkdown("drafting", { brief_markdown: brief })).toBe(
      brief.trim(),
    );
  });

  it("returns empty string when brief_markdown is empty", () => {
    expect(stepResultToMarkdown("drafting", { brief_markdown: "" })).toBe("");
  });

  it("returns empty string when brief_markdown key is missing", () => {
    expect(stepResultToMarkdown("drafting", {})).toBe("");
  });

  it("preserves all required section headers", () => {
    const md = stepResultToMarkdown("drafting", { brief_markdown: brief })!;
    for (const heading of [
      "## FACTS",
      "## ISSUES FOR DETERMINATION",
      "## LEGAL ARGUMENTS",
      "## RESPONDENT'S ANTICIPATED POSITION",
      "## CONCLUSION AND PRAYER FOR RELIEF",
    ]) {
      expect(md).toContain(heading);
    }
  });
});

// ── qa ────────────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — qa", () => {
  const base = {
    hallucination_warnings: [],
    missing_logic: [],
    risk_notes: [],
  };

  it("renders LOW risk level", () => {
    expect(
      stepResultToMarkdown("qa", { ...base, risk_level: "LOW" }),
    ).toContain("LOW");
  });

  it("renders HIGH risk level", () => {
    expect(
      stepResultToMarkdown("qa", { ...base, risk_level: "HIGH" }),
    ).toContain("HIGH");
  });

  it("shows 'None noted' for all three lists when empty", () => {
    const md = stepResultToMarkdown("qa", { ...base, risk_level: "LOW" })!;
    expect(md.match(/None noted/g)?.length).toBeGreaterThanOrEqual(3);
  });

  it("renders a populated hallucination warning", () => {
    const warning = "Statute section cited does not exist in the Act.";
    const md = stepResultToMarkdown("qa", {
      ...base,
      risk_level: "HIGH",
      hallucination_warnings: [warning],
    });
    expect(md).toContain(warning);
  });

  it("renders missing logic and risk notes entries", () => {
    const md = stepResultToMarkdown("qa", {
      risk_level: "MEDIUM",
      hallucination_warnings: [],
      missing_logic: ["Issue 2 never argued"],
      risk_notes: ["Review before filing"],
    })!;
    expect(md).toContain("Issue 2 never argued");
    expect(md).toContain("Review before filing");
  });

  it("shows UNKNOWN when risk_level is missing", () => {
    expect(stepResultToMarkdown("qa", { ...base })).toContain("UNKNOWN");
  });
});
