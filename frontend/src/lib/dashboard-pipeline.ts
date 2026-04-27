import type { HistoryDetail } from "@/lib/api";

export function stepStatus(
  detail: HistoryDetail,
  stepName: string,
): string | undefined {
  return detail.steps.find((s) => s.step_name === stepName)?.status;
}

export type DashboardPipelineState = {
  factsComplete: boolean;
  strategyComplete: boolean;
  briefComplete: boolean;
  /**
   * 0 = Facts, 1 = Strategy, 2 = Brief — first incomplete stage.
   * `null` when every stage is complete.
   */
  currentStageIndex: number | null;
};

export function derivePipelineState(detail: HistoryDetail): DashboardPipelineState {
  const ok = (name: string) => stepStatus(detail, name) === "COMPLETED";

  const factsComplete = ok("extraction") && ok("rag_retrieval");
  const strategyComplete = ok("strategy");
  const briefComplete = ok("drafting") && ok("qa");

  let currentStageIndex: number | null = null;
  if (!factsComplete) currentStageIndex = 0;
  else if (!strategyComplete) currentStageIndex = 1;
  else if (!briefComplete) currentStageIndex = 2;
  else currentStageIndex = null;

  return {
    factsComplete,
    strategyComplete,
    briefComplete,
    currentStageIndex,
  };
}

export function countEntitiesFromExtraction(detail: HistoryDetail): number {
  const extraction = detail.steps.find((s) => s.step_name === "extraction");
  if (!extraction?.result || extraction.status !== "COMPLETED") return 0;
  const r = extraction.result as { entities?: unknown[] };
  return Array.isArray(r.entities) ? r.entities.length : 0;
}
