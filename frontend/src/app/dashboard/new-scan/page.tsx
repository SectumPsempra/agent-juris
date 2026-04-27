"use client";

import {
  useCallback,
  useRef,
  useState,
  type Dispatch,
  type FormEvent,
  type SetStateAction,
} from "react";
import {
  PipelineMarkdownPanel,
  type MarkdownSection,
} from "@/components/pipeline-markdown-panel";
import { type SseAnalyzePayload } from "@/lib/api";
import { useApiClient } from "@/lib/useApiClient";

function handleStreamPayload(
  payload: SseAnalyzePayload,
  setSections: Dispatch<SetStateAction<MarkdownSection[]>>,
  setError: (msg: string | null) => void,
) {
  if (payload.type === "markdown_section") {
    setSections((prev) => {
      const idx = prev.findIndex((s) => s.section_id === payload.section_id);
      const row: MarkdownSection = {
        section_id: payload.section_id,
        heading: payload.heading,
        markdown: payload.markdown,
      };
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = row;
        return next;
      }
      return [...prev, row];
    });
    return;
  }
  if (payload.type === "error") {
    setError(payload.detail);
  }
}

export default function NewScanPage() {
  const { postAnalyzeStream } = useApiClient();

  const [title, setTitle] = useState("");
  const [caseText, setCaseText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [sections, setSections] = useState<MarkdownSection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const onStreamPayload = useCallback((payload: SseAnalyzePayload) => {
    handleStreamPayload(payload, setSections, setError);
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSections([]);

    const t = title.trim();
    if (!t) {
      setError("Name of litigation is required.");
      return;
    }
    if (!caseText.trim() && !file) {
      setError("Enter case text and/or attach a file (.txt, .md, or .pdf).");
      return;
    }

    setLoading(true);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      await postAnalyzeStream(
        { title: t, caseText: caseText, file },
        abortRef.current.signal,
        onStreamPayload,
        (msg) => setError(msg),
      );
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-4 -mx-6 px-6 pb-2">
      <div className="shrink-0">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          New scan
        </h1>
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid min-h-0 w-full flex-1 grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8"
      >
        <div className="flex min-h-0 min-w-0 flex-col gap-6 overflow-y-auto pr-1 lg:max-h-[calc(100svh-10rem)]">
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Matter details
            </h2>
            <label
              htmlFor="litigation-title"
              className="mb-1 block text-sm font-medium text-gray-800 dark:text-gray-200"
            >
              Name of litigation <span className="text-red-500">*</span>
            </label>

            <input
              id="litigation-title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              placeholder="e.g. Acme Ltd v. Board of Directors"
            />
            <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Case file
              </h2>
              <input
                type="file"
                accept=".txt,.md,.pdf,text/plain,application/pdf"
                className="block w-full cursor-pointer text-sm text-gray-700 file:mr-4 file:rounded-lg file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100 dark:text-gray-300 dark:file:bg-blue-950 dark:file:text-blue-200"
                onChange={(ev) => {
                  const f = ev.target.files?.[0] ?? null;
                  setFile(f);
                }}
              />
              {file ? (
                <p
                  className="mt-2 truncate text-xs text-gray-500"
                  title={file.name}
                >
                  Selected: {file.name}
                </p>
              ) : (
                <p className="mt-2 text-xs text-gray-500">
                  Optional — .txt, .md, or .pdf
                </p>
              )}
            </section>
            <label
              htmlFor="case-text"
              className="mb-1 block text-sm font-medium text-gray-800 dark:text-gray-200"
            >
              Case text
            </label>
            <textarea
              id="case-text"
              value={caseText}
              onChange={(e) => setCaseText(e.target.value)}
              rows={12}
              className="min-h-[200px] w-full flex-1 resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              placeholder="Facts, parties, chronology, issues… (optional if you attach a file)"
            />
          </section>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={loading}
              className="cursor-pointer rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white shadow-sm transition-all duration-150 ease-out hover:bg-blue-700 hover:shadow-md active:scale-[0.98] active:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Streaming…" : "Run Litigation Pipeline"}
            </button>
            {loading ? (
              <button
                type="button"
                onClick={handleStop}
                className="cursor-pointer rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800"
              >
                Stop
              </button>
            ) : null}
          </div>

          {error ? (
            <div
              className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200"
              role="alert"
            >
              {error}
            </div>
          ) : null}
        </div>

        <section className="flex min-h-[min(420px,calc(100svh-10rem))] min-w-0 flex-col rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/80">
          <div className="shrink-0 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Litigation Brief Output
            </h2>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">
            <PipelineMarkdownPanel
              sections={sections}
              streaming={loading}
              emptyMessage="Run the pipeline to see streamed Markdown here."
            />
          </div>
        </section>
      </form>
    </div>
  );
}
