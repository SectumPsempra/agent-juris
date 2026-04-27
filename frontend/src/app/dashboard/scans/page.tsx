"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { type HistoryItem } from "@/lib/api";
import { useApiClient } from "@/lib/useApiClient";

function truncateCaseText(s: string, maxLen = 140) {
  const t = s.replace(/\s+/g, " ").trim();
  if (t.length <= maxLen) return t;
  return `${t.slice(0, maxLen)}…`;
}

export default function ScansPage() {
  const router = useRouter();
  const { isLoaded, getCases, deleteCase } = useApiClient();

  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    if (!isLoaded) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCases(debouncedSearch || undefined);
        if (!cancelled) setItems(data);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load scans");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, debouncedSearch, getCases]);

  async function handleDelete(caseId: string) {
    if (!confirm("Delete this scan? This cannot be undone.")) return;
    setDeletingId(caseId);
    setError(null);
    try {
      await deleteCase(caseId);
      setItems((prev) => prev.filter((r) => r.id !== caseId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-4 -mx-6 px-6 pb-2">
      <div className="shrink-0">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Scans
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Search by matter title. Click a row to open details.
        </p>
      </div>

      <div className="max-w-5xl shrink-0">
        <label htmlFor="scan-search" className="sr-only">
          Search by title
        </label>
        <input
          id="scan-search"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title…"
          className="w-full max-w-md rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
        />
      </div>

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : error ? (
        <p className="text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      ) : items.length === 0 ? (
        <p className="text-gray-600 dark:text-gray-400">
          {debouncedSearch ? (
            <>No scans match that title.</>
          ) : (
            <>
              No scans yet.{" "}
              <Link
                href="/dashboard/new-scan"
                className="font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                Run a new scan
              </Link>
              .
            </>
          )}
        </p>
      ) : (
        <div className="min-w-0 overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
          <table className="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/80">
                <th className="px-4 py-3 font-semibold text-gray-900 dark:text-gray-100">
                  Title
                </th>
                <th className="px-4 py-3 font-semibold text-gray-900 dark:text-gray-100">
                  Case text
                </th>
                <th className="w-44 px-4 py-3 font-semibold text-gray-900 dark:text-gray-100">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {items.map((row) => (
                <tr
                  key={row.id}
                  role="link"
                  tabIndex={0}
                  onClick={() => router.push(`/dashboard/scans/${row.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      router.push(`/dashboard/scans/${row.id}`);
                    }
                  }}
                  className="cursor-pointer text-gray-800 transition-colors hover:bg-blue-50/60 focus-visible:bg-blue-50/60 focus-visible:outline-none dark:text-gray-200 dark:hover:bg-gray-800/80 dark:focus-visible:bg-gray-800/80"
                >
                  <td className="max-w-[220px] px-4 py-3 align-top">
                    <span className="line-clamp-2 font-medium text-gray-900 dark:text-gray-100">
                      {row.title}
                    </span>
                  </td>
                  <td
                    className="max-w-md px-4 py-3 align-top text-gray-600 dark:text-gray-400"
                    title={row.raw_input}
                  >
                    {truncateCaseText(row.raw_input)}
                  </td>
                  <td className="px-4 py-3 align-top" onClick={(e) => e.stopPropagation()}>
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={`/dashboard/scans/${row.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-800 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-gray-800"
                      >
                        View
                      </Link>
                      <button
                        type="button"
                        disabled={deletingId === row.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleDelete(row.id);
                        }}
                        className="rounded-md border border-red-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-red-700 shadow-sm hover:bg-red-50 disabled:opacity-50 dark:border-red-900/60 dark:bg-gray-900 dark:text-red-300 dark:hover:bg-red-950/40"
                      >
                        {deletingId === row.id ? "…" : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
