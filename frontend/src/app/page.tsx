"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { SignedIn, SignedOut, useAuth } from "@clerk/nextjs";

import { MarketingLanding } from "@/components/marketing-landing";

function SignedInRedirectToDashboard() {
  const router = useRouter();
  const { isLoaded, userId } = useAuth();

  useEffect(() => {
    if (isLoaded && userId) {
      router.replace("/dashboard");
    }
  }, [isLoaded, userId, router]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center text-gray-500 dark:text-gray-400">
      Opening workspace…
    </div>
  );
}

export default function Home() {
  return (
    <>
      <SignedOut>
        <main className="bg-white dark:bg-gray-950">
          <MarketingLanding />
        </main>
      </SignedOut>

      <SignedIn>
        <SignedInRedirectToDashboard />
      </SignedIn>
    </>
  );
}
