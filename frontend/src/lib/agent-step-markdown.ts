/**
 * Mirrors `backend/src/agents/format_markdown.py` so stored step JSON
 * renders the same Markdown as the live SSE stream.
 */

export const STEP_HEADINGS: Record<string, string> = {
  extraction: "Fact extraction",
  rag_retrieval: "Precedent retrieval",
  strategy: "Legal strategy",
  drafting: "Draft brief",
  qa: "Quality review",
};

function asStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x): x is string => typeof x === "string");
}

function extractionToMarkdown(result: Record<string, unknown>): string {
  const lines: string[] = ["### Core facts", ""];
  for (const fact of asStringArray(result.core_facts)) {
    lines.push(`- ${fact}`);
  }
  lines.push("", "### Entities", "");
  const entities = Array.isArray(result.entities) ? result.entities : [];
  for (const ent of entities) {
    if (!ent || typeof ent !== "object") continue;
    const e = ent as Record<string, unknown>;
    const name = typeof e.name === "string" ? e.name : "";
    const type = typeof e.type === "string" ? e.type : "";
    const role = typeof e.role === "string" ? e.role : "";
    lines.push(`- **${name}** — _${type}_ — ${role}`);
  }
  lines.push("", "### Chronological timeline", "");
  const timeline = Array.isArray(result.chronological_timeline)
    ? result.chronological_timeline
    : [];
  for (const ev of timeline) {
    if (!ev || typeof ev !== "object") continue;
    const t = ev as Record<string, unknown>;
    const date = typeof t.date === "string" ? t.date : "";
    const event = typeof t.event === "string" ? t.event : "";
    lines.push(`- **${date}** — ${event}`);
  }
  return lines.join("\n").trim();
}

function ragChunksToMarkdown(result: Record<string, unknown>): string {
  const chunks = asStringArray(result.chunks);
  if (chunks.length === 0) {
    return "_No precedents were retrieved for this matter._\n";
  }
  const lines: string[] = ["### Retrieved excerpts", ""];
  chunks.forEach((chunk, i) => {
    lines.push(`#### Source ${i + 1}`, "", (chunk || "_(empty)_").trim(), "");
  });
  return lines.join("\n").trim();
}

function strategyToMarkdown(result: Record<string, unknown>): string {
  const lines: string[] = ["### Legal issues", ""];
  for (const issue of asStringArray(result.legal_issues)) {
    lines.push(`- ${issue}`);
  }
  lines.push("", "### Applicable laws", "");
  for (const law of asStringArray(result.applicable_laws)) {
    lines.push(`- ${law}`);
  }
  lines.push("", "### Arguments", "");
  const args = Array.isArray(result.arguments) ? result.arguments : [];
  for (const arg of args) {
    if (!arg || typeof arg !== "object") continue;
    const a = arg as Record<string, unknown>;
    const issue = typeof a.issue === "string" ? a.issue : "";
    const law =
      typeof a.applicable_kenyan_law === "string" ? a.applicable_kenyan_law : "";
    const summary =
      typeof a.argument_summary === "string" ? a.argument_summary : "";
    lines.push(`- **${issue}**  `);
    lines.push(`  - Law: ${law}`);
    lines.push(`  - Summary: ${summary}`);
    lines.push("");
  }
  lines.push("", "### Counterarguments", "");
  for (const c of asStringArray(result.counterarguments)) {
    lines.push(`- ${c}`);
  }
  const reasoning =
    typeof result.legal_reasoning === "string"
      ? result.legal_reasoning.trim()
      : "";
  lines.push("", "### Legal reasoning", "", reasoning);
  return lines.join("\n").trim();
}

function draftingToMarkdown(result: Record<string, unknown>): string {
  const md =
    typeof result.brief_markdown === "string" ? result.brief_markdown.trim() : "";
  return md;
}

function qaToMarkdown(result: Record<string, unknown>): string {
  const risk =
    typeof result.risk_level === "string" ? result.risk_level : "UNKNOWN";
  const lines: string[] = [`**Risk level:** \`${risk}\``, "", "### Hallucination warnings", ""];
  const hw = asStringArray(result.hallucination_warnings);
  if (hw.length) lines.push(...hw.map((w) => `- ${w}`));
  else lines.push("- _None noted_");
  lines.push("", "### Missing logic", "");
  const ml = asStringArray(result.missing_logic);
  if (ml.length) lines.push(...ml.map((m) => `- ${m}`));
  else lines.push("- _None noted_");
  lines.push("", "### Risk notes", "");
  const rn = asStringArray(result.risk_notes);
  if (rn.length) lines.push(...rn.map((n) => `- ${n}`));
  else lines.push("- _None noted_");
  return lines.join("\n").trim();
}

export function stepResultToMarkdown(
  stepName: string,
  result: Record<string, unknown> | null,
): string | null {
  if (!result) return null;
  switch (stepName) {
    case "extraction":
      return extractionToMarkdown(result);
    case "rag_retrieval":
      return ragChunksToMarkdown(result);
    case "strategy":
      return strategyToMarkdown(result);
    case "drafting":
      return draftingToMarkdown(result);
    case "qa":
      return qaToMarkdown(result);
    default:
      return null;
  }
}
