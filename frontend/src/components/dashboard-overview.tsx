"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useUser } from "@clerk/nextjs";

import type { HistoryDetail, HistoryItem } from "@/lib/api";
import {
  countEntitiesFromExtraction,
  derivePipelineState,
} from "@/lib/dashboard-pipeline";
import { useApiClient } from "@/lib/useApiClient";

const DETAIL_LOOKBACK = 28;
const RECENT_SHOWN = 5;

function greetingWord(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  const diff = Date.now() - t;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? "" : "s"} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function displayName(
  user:
    | { firstName?: string | null; username?: string | null }
    | null
    | undefined,
): string {
  if (!user) return "there";
  const first = user.firstName?.trim();
  if (first) return first;
  const u = user.username?.trim();
  if (u) return u;
  return "there";
}

function caseStatusLine(detail: HistoryDetail): string {
  const rel = formatRelative(detail.created_at);
  if (detail.status === "COMPLETED") return `Updated ${rel} · Complete`;
  if (detail.status === "FAILED") return `Updated ${rel} · Needs attention`;
  return `Updated ${rel} · In progress`;
}

const CASE_ICONS = ["¶", "⚖️", "📄"];

function PipelinePills({ detail }: { detail: HistoryDetail }) {
  const s = derivePipelineState(detail);
  const stages: { label: string; idx: 0 | 1 | 2 }[] = [
    { label: "Facts", idx: 0 },
    { label: "Strategy", idx: 1 },
    { label: "Brief", idx: 2 },
  ];

  const done = [s.factsComplete, s.strategyComplete, s.briefComplete];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {stages.map(({ label, idx }) => {
        const isDone = done[idx];
        const isCurrent = s.currentStageIndex === idx;

        let cls =
          "rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors";
        if (isDone && !isCurrent) {
          cls +=
            " border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800/80 dark:bg-emerald-950/40 dark:text-emerald-200";
        } else if (isCurrent) {
          if (idx === 0) {
            cls +=
              " border-emerald-300 bg-emerald-100 text-emerald-950 dark:border-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-50";
          } else {
            cls +=
              " border-blue-300 bg-blue-100 text-blue-950 dark:border-blue-600 dark:bg-blue-950/50 dark:text-blue-100";
          }
        } else {
          cls +=
            " border-stone-200 bg-stone-100/80 text-stone-500 dark:border-white/10 dark:bg-white/5 dark:text-white/40";
        }

        return (
          <span key={label} className={cls}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

export function DashboardOverview() {
  const { user, isLoaded: userLoaded } = useUser();
  const { isLoaded, getCases, getCase } = useApiClient();

  const [items, setItems] = useState<HistoryItem[]>([]);
  const [details, setDetails] = useState<HistoryDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await getCases();
        if (cancelled) return;
        setItems(list);

        const ids = list.slice(0, DETAIL_LOOKBACK).map((c) => c.id);
        const settled = await Promise.allSettled(ids.map((id) => getCase(id)));
        if (cancelled) return;
        const ok: HistoryDetail[] = [];
        for (let i = 0; i < settled.length; i++) {
          const r = settled[i];
          if (r.status === "fulfilled") ok.push(r.value);
        }
        setDetails(ok);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, getCases, getCase]);

  /** Open work: anything not successfully completed. */
  const activeCount = useMemo(
    () => items.filter((c) => c.status !== "COMPLETED").length,
    [items],
  );

  const stats = useMemo(() => {
    const inBriefing = details.filter(
      (d) => d.status !== "COMPLETED" && !derivePipelineState(d).briefComplete,
    ).length;
    const briefsDrafted = details.filter((d) =>
      d.steps.some(
        (s) => s.step_name === "drafting" && s.status === "COMPLETED",
      ),
    ).length;
    const factsExtracted = details.reduce(
      (acc, d) => acc + countEntitiesFromExtraction(d),
      0,
    );
    const pendingReview = details.filter((d) => {
      const qa = d.steps.find((s) => s.step_name === "qa");
      const draft = d.steps.find((s) => s.step_name === "drafting");
      return draft?.status === "COMPLETED" && qa && qa.status !== "COMPLETED";
    }).length;

    return {
      inBriefing,
      briefsDrafted,
      factsExtracted,
      pendingReview,
    };
  }, [details]);

  const lastActivity = useMemo(() => {
    if (items.length === 0) return null;
    const latest = items.reduce((a, b) =>
      new Date(a.created_at) > new Date(b.created_at) ? a : b,
    );
    return formatRelative(latest.created_at);
  }, [items]);

  const recent = details.slice(0, RECENT_SHOWN);

  const statCards = [
    {
      label: "Active cases",
      value: String(activeCount),
      hint:
        stats.inBriefing > 0
          ? `${stats.inBriefing} in briefing`
          : activeCount
            ? "In pipeline"
            : "All caught up",
    },
    {
      label: "Briefs drafted",
      value: String(stats.briefsDrafted),
      hint: "From recent scans",
    },
    {
      label: "Facts extracted",
      value: String(stats.factsExtracted),
      hint: "Entities in recent scans",
    },
    {
      label: "Pending review",
      value: String(stats.pendingReview),
      hint: "QA not signed off",
    },
  ];

  if (!userLoaded || !isLoaded) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">Loading…</div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-10 pb-4">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-stone-900 dark:text-stone-100 sm:text-3xl">
            {greetingWord()}, {displayName(user)}
          </h1>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
            {items.length === 0 ? (
              <>No scans yet — start with a new scan.</>
            ) : (
              <>
                {activeCount} active {activeCount === 1 ? "case" : "cases"}
                {lastActivity ? ` · Last activity ${lastActivity}` : ""}
              </>
            )}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Link
            href="/dashboard/new-scan"
            className="inline-flex items-center justify-center rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold text-stone-800 shadow-sm transition hover:bg-stone-50 dark:border-white/15 dark:bg-stone-900 dark:text-stone-100 dark:hover:bg-stone-800"
          >
            + New scan
          </Link>
        </div>
      </header>

      {error ? (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      ) : null}

      <section aria-label="Summary">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((c) => (
            <div
              key={c.label}
              className="rounded-2xl border border-stone-200/80 bg-[#f9f9f7] p-4 shadow-sm dark:border-white/10 dark:bg-stone-900/60"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-stone-500 dark:text-stone-400">
                {c.label}
              </p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-stone-900 dark:text-stone-50">
                {loading ? "—" : c.value}
              </p>
              <p className="mt-1 text-xs text-stone-600 dark:text-stone-400">
                {loading ? "…" : c.hint}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Recent cases">
        <div className="mb-3 flex items-end justify-between gap-2">
          <h2 className="text-lg font-semibold text-stone-900 dark:text-stone-100">
            Recent cases
          </h2>
          <Link
            href="/dashboard/scans"
            className="text-sm font-medium text-blue-700 hover:underline dark:text-blue-400"
          >
            View all
          </Link>
        </div>

        {loading ? (
          <p className="text-sm text-stone-500">Loading cases…</p>
        ) : recent.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-stone-300 bg-[#f9f9f7] px-6 py-10 text-center dark:border-white/15 dark:bg-stone-900/40">
            <p className="text-sm text-stone-600 dark:text-stone-400">
              No cases yet.{" "}
              <Link
                className="font-medium text-blue-700 hover:underline dark:text-blue-400"
                href="/dashboard/new-scan"
              >
                Run your first scan
              </Link>
              .
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-3">
            {recent.map((detail, i) => (
              <li
                key={detail.id}
                className="flex flex-col gap-3 rounded-2xl border border-stone-200/80 bg-[#f9f9f7] p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between dark:border-white/10 dark:bg-stone-900/60"
              >
                <div className="flex min-w-0 flex-1 gap-3">
                  <span
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm ring-1 ring-stone-200 dark:bg-stone-800 dark:ring-white/10"
                    aria-hidden
                  >
                    {CASE_ICONS[i % CASE_ICONS.length]}
                  </span>
                  <div className="min-w-0">
                    <p className="font-semibold text-stone-900 dark:text-stone-100">
                      {detail.title}
                    </p>
                    <p className="mt-0.5 text-xs text-stone-600 dark:text-stone-400">
                      {caseStatusLine(detail)}
                    </p>
                    <div className="mt-2">
                      <PipelinePills detail={detail} />
                    </div>
                  </div>
                </div>
                <Link
                  href={`/dashboard/scans/${detail.id}`}
                  className="inline-flex shrink-0 items-center justify-center gap-1 rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 shadow-sm transition hover:bg-stone-50 dark:border-white/15 dark:bg-stone-800 dark:text-stone-100 dark:hover:bg-stone-700"
                >
                  Resume <span aria-hidden>↗</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Quick actions">
        <h2 className="mb-3 text-lg font-semibold text-stone-900 dark:text-stone-100">
          Quick actions
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Link
            href="/dashboard/new-scan"
            className="group rounded-2xl border border-stone-200/80 bg-[#f9f9f7] p-5 shadow-sm transition hover:border-stone-300 hover:shadow-md dark:border-white/10 dark:bg-stone-900/60 dark:hover:border-white/20"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-semibold text-stone-900 dark:text-stone-100">
                Upload case notes
              </h3>
              <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-800 dark:bg-violet-950/60 dark:text-violet-200">
                Guide
              </span>
            </div>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-400">
              Drop PDFs, scanned affidavits, or typed notes — the pipeline
              extracts facts and entities automatically.
            </p>
          </Link>
          <a
            href="https://www.kenyalaw.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-2xl border border-stone-200/80 bg-[#f9f9f7] p-5 shadow-sm transition hover:border-stone-300 hover:shadow-md dark:border-white/10 dark:bg-stone-900/60 dark:hover:border-white/20"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-semibold text-stone-900 dark:text-stone-100">
                Kenyan law search
              </h3>
              <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-900 dark:bg-sky-950/60 dark:text-sky-200">
                New
              </span>
            </div>
            <p className="mt-2 text-sm text-stone-600 dark:text-stone-400">
              Open Kenya Law for statutes, cap references, and reported
              decisions (external site).
            </p>
          </a>
        </div>
      </section>
    </div>
  );
}
