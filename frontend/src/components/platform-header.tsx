import Link from "next/link";

import { LitigationPrepMark } from "@/components/litigation-prep-mark";

export function PlatformHeader() {
  return (
    <header className="sticky top-0 z-50 shrink-0 border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-[#1a222f]">
      <div className="mx-auto flex h-12 max-w-[1920px] items-center px-4 sm:px-6">
        <Link
          href="/"
          className="flex cursor-pointer items-center md:hidden"
          aria-label="Litigation Prep Assistant home"
        >
          <LitigationPrepMark className="h-9 w-9" />
        </Link>
        <Link
          href="/"
          className="hidden cursor-pointer text-lg font-semibold tracking-tight text-gray-900 transition-colors hover:text-blue-700 md:inline dark:text-gray-100 dark:hover:text-blue-300"
        >
          Litigation Prep Assistant
        </Link>
      </div>
    </header>
  );
}
