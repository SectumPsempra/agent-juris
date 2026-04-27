"use client";

import React from "react";
import { SignedIn, SignedOut } from "@clerk/nextjs";

import { AppShell } from "@/components/app-shell";

export function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SignedOut>{children}</SignedOut>
      <SignedIn>
        <div className="flex min-h-0 flex-1 flex-col">
          <AppShell>{children}</AppShell>
        </div>
      </SignedIn>
    </>
  );
}
