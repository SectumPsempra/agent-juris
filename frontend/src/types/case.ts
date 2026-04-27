export interface AgentStep {
  agent: string;
  status: "pending" | "running" | "completed" | "failed";
  data?: Record<string, unknown>;
}

export interface FinalBrief {
  caseSummary: string;
  legalIssues: string[];
  argumentsForClient: string[];
  risks: string[];
  recommendations: string[];
}

export interface CaseResult {
  id: string;
  title: string;
  caseText: string;
  steps: AgentStep[];
  finalBrief?: FinalBrief;
}
