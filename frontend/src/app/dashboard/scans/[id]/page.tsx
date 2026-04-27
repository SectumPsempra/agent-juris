"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  PipelineMarkdownPanel,
  type MarkdownSection,
} from "@/components/pipeline-markdown-panel";
import { STEP_HEADINGS, stepResultToMarkdown } from "@/lib/agent-step-markdown";
import { type HistoryDetail } from "@/lib/api";
import { useApiClient } from "@/lib/useApiClient";

export default function ScanDetailPage() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";
  const { isLoaded, getCase } = useApiClient();

  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded || !id) return;
    let cancelled = false;
    void (async () => {
      setLoading(true);
      setError(null);
      setDetail(null);
      try {
        const data = await getCase(id);
        if (!cancelled) setDetail(data);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, id, getCase]);

  const sections: MarkdownSection[] = useMemo(() => {
    if (!detail?.steps?.length) return [];
    return [...detail.steps]
      .sort((a, b) => a.step_index - b.step_index)
      .map((s) => {
        const md = stepResultToMarkdown(s.step_name, s.result);
        if (!md) return null;
        return {
          section_id: s.step_name,
          heading: STEP_HEADINGS[s.step_name] ?? s.step_name,
          markdown: md,
        };
      })
      .filter((x): x is MarkdownSection => x !== null);
  }, [detail]);

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-4 -mx-6 px-6 pb-2">
      <div className="shrink-0">
        <Link
          href="/dashboard/scans"
          className="mb-2 inline-block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
        >
          ← All scans
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {detail && detail.id === id ? detail.title : "Scan detail"}
        </h1>
        <p className="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">
          {id || "—"}
        </p>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : error ? (
        <p className="text-red-600 dark:text-red-400">{error}</p>
      ) : detail ? (
        <div className="grid min-h-0 w-full flex-1 grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8">
          <div className="flex min-h-0 min-w-0 flex-col gap-6 overflow-y-auto pr-1 lg:max-h-[calc(100svh-10rem)]">
            <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Metadata
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {new Date(detail.created_at).toLocaleString()}
              </p>
              <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                Status: {detail.status}
              </p>
            </section>

            <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Raw input
              </h2>
              <p className="min-h-[120px] flex-1 whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200">
                {detail.raw_input}
              </p>
            </section>
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
                emptyMessage="No Litigation Brief to show."
              />
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
