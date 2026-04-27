"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LitigationPrepMark } from "@/components/litigation-prep-mark";

const shell = "bg-[#1a222f] text-white";

function IconHome({ className }: { className?: string }) {
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
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  );
}

function IconScan({ className }: { className?: string }) {
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
        d="M12 4v16m8-8H4"
      />
    </svg>
  );
}

function IconList({ className }: { className?: string }) {
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
        d="M4 6h16M4 12h16M4 18h7"
      />
    </svg>
  );
}

function IconPlans({ className }: { className?: string }) {
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
        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
      />
    </svg>
  );
}

function NavRow({
  href,
  icon,
  label,
  active,
  onNavigate,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={() => onNavigate?.()}
      className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors ${
        active
          ? "bg-blue-600 text-white shadow-md ring-1 ring-blue-400/40"
          : "text-white/80 hover:bg-white/5 hover:text-white"
      }`}
    >
      <span className="flex h-5 w-5 shrink-0 items-center justify-center opacity-90">
        {icon}
      </span>
      {label}
    </Link>
  );
}

export function AppSidebar({
  id,
  className = "",
  onNavigate,
}: {
  id?: string;
  className?: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const homeActive = pathname === "/dashboard" || pathname === "/dashboard/";
  const newScanActive = pathname === "/dashboard/new-scan";
  const scansActive = pathname.startsWith("/dashboard/scans");
  const plansActive = pathname.startsWith("/subscriptions");
  return (
    <aside
      id={id}
      className={`flex w-64 shrink-0 flex-col overflow-y-auto border-r border-white/10 md:min-h-[calc(100svh-3rem)] md:self-stretch ${shell} ${className}`}
    >
      <div className="border-b border-white/10 px-4 py-4">
        <Link
          href="/dashboard"
          onClick={() => onNavigate?.()}
          className="flex items-center gap-3 rounded-lg outline-none ring-blue-400/60 transition-colors hover:bg-white/5 focus-visible:ring-2"
        >
          <LitigationPrepMark className="h-11 w-11 shrink-0" />
          <div className="hidden min-w-0 md:block">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/50">
              Litigation Prep
            </p>
            <p className="mt-0.5 text-lg font-bold leading-tight text-white">
              Assistant
            </p>
          </div>
        </Link>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        <NavRow
          href="/dashboard"
          label="Home"
          icon={<IconHome className="h-5 w-5" />}
          active={homeActive}
          onNavigate={onNavigate}
        />
        <NavRow
          href="/dashboard/new-scan"
          label="New Scan"
          icon={<IconScan className="h-5 w-5" />}
          active={newScanActive}
          onNavigate={onNavigate}
        />
        <NavRow
          href="/dashboard/scans"
          label="Scans"
          icon={<IconList className="h-5 w-5" />}
          active={scansActive}
          onNavigate={onNavigate}
        />
        <NavRow
          href="/subscriptions"
          label="Plans"
          icon={<IconPlans className="h-5 w-5" />}
          active={plansActive}
          onNavigate={onNavigate}
        />
      </nav>
    </aside>
  );
}
