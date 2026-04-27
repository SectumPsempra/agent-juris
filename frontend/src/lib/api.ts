export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** One completed pipeline step — Markdown body only (heading is separate for UI). */
export type SseMarkdownSection = {
  type: "markdown_section";
  section_id: string;
  heading: string;
  markdown: string;
};

export type SseAnalyzeComplete = {
  type: "complete";
  case_id: string;
};

export type SseAnalyzeError = {
  type: "error";
  detail: string;
};

export type SseAnalyzePayload =
  | SseMarkdownSection
  | SseAnalyzeComplete
  | SseAnalyzeError;

export type AnalyzeFormInput = {
  title: string;
  caseText: string;
  file: File | null;
};

/** POST `/api/v1/analyze` — `multipart/form-data` + `StreamingResponse` (`text/event-stream`). */
export async function postAnalyzeStream(
  input: AnalyzeFormInput,
  userId: string | undefined,
  token: string | null,
  signal: AbortSignal,
  onSseData: (payload: SseAnalyzePayload) => void,
  onError: (message: string) => void,
): Promise<void> {
  const fd = new FormData();
  fd.append("title", input.title.trim());
  fd.append("case_text", input.caseText);
  if (input.file) {
    fd.append("case_file", input.file);
  }

  const res = await fetch(`${apiBaseUrl}/api/v1/analyze`, {
    method: "POST",
    signal,
    headers: {
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: fd,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    onError(text || `Request failed (${res.status})`);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    onError("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  const parseSseBlock = (block: string) => {
    for (const line of block.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const json = trimmed.slice(5).trim();
      if (!json) continue;
      try {
        const payload = JSON.parse(json) as SseAnalyzePayload;
        onSseData(payload);
      } catch {
        onError("Invalid SSE payload");
      }
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (value) buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const block of parts) {
        parseSseBlock(block);
      }

      if (done) {
        if (buffer.trim()) parseSseBlock(buffer);
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export type HistoryItem = {
  id: string;
  title: string;
  raw_input: string;
  status: string;
  created_at: string;
};

/** `titleSearch` filters by case title (substring, case-insensitive); backend only. */
export async function getCases(
  token: string | null,
  userId: string | undefined,
  titleSearch?: string,
): Promise<HistoryItem[]> {
  const params = new URLSearchParams();
  const q = titleSearch?.trim();
  if (q) params.set("q", q);
  const qs = params.toString();
  const res = await fetch(
    `${apiBaseUrl}/api/v1/cases${qs ? `?${qs}` : ""}`,
    {
      headers: {
        ...(userId ? { "X-User-Id": userId } : {}),
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new Error(await res.text().catch(() => `HTTP ${res.status}`));
  }
  return res.json() as Promise<HistoryItem[]>;
}

export async function deleteCase(
  id: string,
  userId: string | undefined,
  token: string | null,
): Promise<void> {
  const res = await fetch(`${apiBaseUrl}/api/v1/cases/${id}`, {
    method: "DELETE",
    headers: {
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) {
    throw new Error(await res.text().catch(() => `HTTP ${res.status}`));
  }
}

export type AgentStepOut = {
  id: string;
  step_name: string;
  step_index: number;
  status: string;
  result: Record<string, unknown> | null;
};

export type HistoryDetail = {
  id: string;
  title: string;
  raw_input: string;
  status: string;
  created_at: string;
  steps: AgentStepOut[];
};

export async function getCase(
  id: string,
  userId: string | undefined,
  token: string | null,
): Promise<HistoryDetail> {
  const res = await fetch(`${apiBaseUrl}/api/v1/cases/${id}`, {
    headers: {
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(await res.text().catch(() => `HTTP ${res.status}`));
  }
  return res.json() as Promise<HistoryDetail>;
}
