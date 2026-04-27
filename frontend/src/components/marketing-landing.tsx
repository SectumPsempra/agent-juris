"use client";

import Link from "next/link";
import { SignInButton } from "@clerk/nextjs";
import { LitigationPrepMark } from "@/components/litigation-prep-mark";

const pipelineSteps = [
  { title: "Your notes", sub: "Text or PDF", emoji: "\u{1F4C4}" },
  { title: "Extraction", sub: "Facts & timeline", emoji: "\u2705" },
  { title: "Strategy", sub: "Kenyan law & RAG", emoji: "\u2696\uFE0F" },
  { title: "Draft brief", sub: "Structured Markdown", emoji: "\u{1F4C4}" },
  { title: "QA audit", sub: "Risk & hallucinations", emoji: "\u2B50" },
] as const;

const testimonials = [
  {
    quote:
      "Used to take me half a day to prep a brief for a commercial dispute. Now I have a solid first draft in under 10 minutes.",
    name: "Amina Waweru",
    role: "Paralegal, Nairobi CBD firm",
    initials: "AW",
  },
  {
    quote:
      "The Kenyan law citations are actually grounded — it pulls from real statutes, not hallucinated references. That matters in court.",
    name: "Kevin Otieno",
    role: "Junior advocate, 2 yrs call",
    initials: "KO",
  },
  {
    quote:
      "The QA audit flag saved me once — caught a fact in the draft that wasn't in the original instructions. That's a real check.",
    name: "Njambi Muthoni",
    role: "Senior partner, Westlands",
    initials: "NM",
  },
] as const;

const beforeBullets = [
  "4–6 hours reading and re-reading case notes to extract facts.",
  "Manual case law lookup across eKLR and statute books.",
  "Freeform draft with no consistent structure across attorneys.",
  "No audit trail — hallucinations or logic gaps go undetected.",
];

const afterBullets = [
  "Facts, entities, and timeline extracted automatically in seconds.",
  "Relevant Kenyan statutes and precedents retrieved via RAG.",
  "Structured brief: facts → issues → arguments → conclusion.",
  "QA agent flags hallucinations and unsourced claims before review.",
];

function navButtonClass(outline: boolean) {
  return outline
    ? "cursor-pointer rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm transition hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-gray-800"
    : "cursor-pointer rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700";
}

export function MarketingLanding() {
  return (
    <div className="bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <div className="border-b border-gray-200/80 bg-white/95 backdrop-blur-md dark:border-white/10 dark:bg-gray-950/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2 sm:px-6 sm:py-2.5">
          <Link
            href="/"
            className="flex min-w-0 cursor-pointer items-center gap-2 text-gray-900 dark:text-white"
          >
            <LitigationPrepMark className="h-9 w-9 shrink-0" />
            <span className="truncate text-lg font-semibold tracking-tight">
              Litigation Prep
            </span>
          </Link>
          <nav className="flex shrink-0 flex-wrap items-center justify-end gap-x-2 gap-y-2 sm:gap-x-4">
            <a
              href="#how-it-works"
              className="hidden cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-900 sm:inline dark:text-gray-400 dark:hover:text-white"
            >
              How it works
            </a>

            <SignInButton mode="modal">
              <button type="button" className={navButtonClass(true)}>
                Sign in
              </button>
            </SignInButton>
            <SignInButton mode="modal">
              <button type="button" className={navButtonClass(false)}>
                Start free trial
              </button>
            </SignInButton>
          </nav>
        </div>
      </div>

      <section className="mx-auto max-w-4xl px-4 pb-10 pt-8 text-center sm:px-6 sm:pb-12 sm:pt-10">
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-900 dark:border-violet-800 dark:bg-violet-950/50 dark:text-violet-200">
          <span
            className="h-1.5 w-1.5 rounded-full bg-violet-600"
            aria-hidden
          />
          Built for Kenyan advocates &amp; paralegals
        </p>
        <h1 className="text-balance text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl lg:text-5xl dark:text-white">
          From messy case notes to a{" "}
          <span className="text-blue-600 dark:text-blue-400">
            court-ready brief
          </span>{" "}
          — in minutes
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-pretty text-base text-gray-600 dark:text-gray-400">
          Paste your facts. Our AI extracts entities, builds a timeline, maps
          Kenyan law, and drafts a structured legal brief — ready for review.
        </p>
        <div className="mt-6 flex flex-col items-center justify-center gap-2.5 sm:flex-row sm:flex-wrap">
          <SignInButton mode="modal">
            <button type="button" className={navButtonClass(true)}>
              Start free trial — no card needed
            </button>
          </SignInButton>
          <a href="#how-it-works" className={navButtonClass(true)}>
            See how it works
          </a>
        </div>
        <p className="mt-4 text-sm text-gray-500 dark:text-gray-500">
          Free for 3 cases · No setup · Kenyan law database included
        </p>
      </section>

      <section
        id="how-it-works"
        className="border-y border-stone-200/80 bg-[#f9f9f5] py-8 dark:border-white/10 dark:bg-stone-900/40 sm:py-10"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
            How your case moves through the pipeline
          </p>
          <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-3 sm:gap-6 lg:grid-cols-5">
            {pipelineSteps.map((step) => (
              <div
                key={step.title}
                className="flex flex-col items-center text-center"
              >
                <span className="text-xl sm:text-2xl" aria-hidden>
                  {step.emoji}
                </span>
                <p className="mt-1.5 text-xs font-semibold text-gray-900 sm:text-sm dark:text-white">
                  {step.title}
                </p>
                <p className="mt-0.5 text-[10px] text-gray-500 sm:text-xs dark:text-gray-400">
                  {step.sub}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-12">
        <div className="grid gap-4 md:grid-cols-3">
          {testimonials.map((t) => (
            <blockquote
              key={t.name}
              className="flex flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-gray-900"
            >
              <p className="flex-1 text-sm italic leading-snug text-gray-700 dark:text-gray-300">
                &ldquo;{t.quote}&rdquo;
              </p>
              <footer className="mt-4 flex items-center gap-2.5">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-800 dark:bg-indigo-950 dark:text-indigo-200">
                  {t.initials}
                </span>
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {t.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t.role}
                  </p>
                </div>
              </footer>
            </blockquote>
          ))}
        </div>
      </section>

      <section className="border-t border-gray-200 bg-gray-50/80 py-10 dark:border-white/10 dark:bg-gray-900/30 sm:py-12">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
            Before &amp; after
          </p>
          <h2 className="mt-1.5 text-center text-2xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-3xl">
            What changes for your workflow
          </h2>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-red-100 bg-white p-4 shadow-sm dark:border-red-900/30 dark:bg-gray-950">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-red-800 dark:bg-red-950/50 dark:text-red-200">
                  Before
                </span>
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  Manual litigation prep
                </span>
              </div>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                {beforeBullets.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                    {line}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-emerald-100 bg-white p-4 shadow-sm dark:border-emerald-900/30 dark:bg-gray-950">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200">
                  After
                </span>
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  LitigationPrep
                </span>
              </div>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                {afterBullets.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-200 bg-white py-6 dark:border-white/10 dark:bg-gray-950 sm:py-7">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-center text-sm text-gray-500 sm:flex-row sm:text-left dark:text-gray-400">
          <p>
            © {new Date().getFullYear()} LitigationPrep · Built for Kenyan legal
            workflows
          </p>
          <nav className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="#"
              className="cursor-pointer hover:text-gray-900 dark:hover:text-white"
            >
              Privacy
            </a>
            <a
              href="#"
              className="cursor-pointer hover:text-gray-900 dark:hover:text-white"
            >
              Terms
            </a>
            <a
              href="#"
              className="cursor-pointer hover:text-gray-900 dark:hover:text-white"
            >
              Contact
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}
