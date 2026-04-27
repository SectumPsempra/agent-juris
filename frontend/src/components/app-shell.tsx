"use client";

import { startTransition, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

import { AppSidebar } from "@/components/app-sidebar";

/** Matches `PlatformHeader` (`h-12`) for full-height shell below the global bar. */
const belowPlatformChrome = "min-h-[calc(100svh-3rem)]";

function IconMenu({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const plansActive = pathname.startsWith("/subscriptions");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    startTransition(() => {
      setMobileNavOpen(false);
    });
  }, [pathname]);

  useEffect(() => {
    if (!mobileNavOpen) return;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileNavOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const onChange = () => {
      if (mq.matches) setMobileNavOpen(false);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const closeMobileNav = () => setMobileNavOpen(false);
  const toggleMobileNav = () => setMobileNavOpen((o) => !o);

  const sidebarMobileClasses = mobileNavOpen
    ? "translate-x-0"
    : "-translate-x-full pointer-events-none md:pointer-events-auto";

  return (
    <div
      className={`relative flex min-h-0 flex-1 bg-gray-50 dark:bg-gray-950 ${belowPlatformChrome}`}
    >
      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Close navigation menu"
          className="fixed top-12 right-0 bottom-0 left-0 z-40 bg-black/50 md:hidden"
          onClick={closeMobileNav}
        />
      ) : null}

      <AppSidebar
        id="app-sidebar-nav"
        onNavigate={closeMobileNav}
        className={`fixed top-12 left-0 z-50 h-[calc(100svh-3rem)] shadow-xl transition-transform duration-200 ease-out md:relative md:top-auto md:z-auto md:h-auto md:translate-x-0 md:shadow-none ${sidebarMobileClasses}`}
      />

      <div className="relative z-0 flex min-h-0 min-w-0 flex-1 flex-col md:z-auto">
        <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-gray-200 bg-white px-3 dark:border-gray-800 dark:bg-[#1a222f] sm:px-4">
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <button
              type="button"
              className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-gray-300 text-gray-800 transition hover:bg-gray-50 md:hidden dark:border-white/20 dark:text-white dark:hover:bg-white/10"
              aria-expanded={mobileNavOpen}
              aria-controls="app-sidebar-nav"
              onClick={toggleMobileNav}
            >
              <IconMenu className="h-5 w-5" />
            </button>
            <Link
              href="/"
              className="hidden min-w-0 truncate text-left text-lg font-semibold text-gray-900 transition-colors hover:text-blue-700 md:inline dark:text-gray-100 dark:hover:text-blue-300"
            >
              Litigation Prep Assistant
            </Link>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <Link
              href="/subscriptions"
              className={`inline-flex items-center gap-2 rounded-lg border px-2.5 py-2 text-sm font-medium transition-colors sm:px-3 ${
                plansActive
                  ? "border-blue-500 bg-blue-50 text-blue-800 dark:border-blue-400 dark:bg-blue-950/50 dark:text-blue-200"
                  : "border-gray-300 text-gray-800 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700 dark:border-white/20 dark:text-white dark:hover:border-blue-400 dark:hover:bg-blue-950/40 dark:hover:text-blue-200"
              }`}
            >
              Plans
            </Link>
            <UserButton showName />
          </div>
        </header>
        <main
          className={`min-h-0 flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 ${
            mobileNavOpen
              ? "invisible pointer-events-none md:visible md:pointer-events-auto"
              : ""
          }`}
          aria-hidden={mobileNavOpen ? true : undefined}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
