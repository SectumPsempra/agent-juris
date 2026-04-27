"use client";
import { PricingTable } from "@clerk/nextjs";

export default function SubscriptionsPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-16 pb-12">
      <section id="plans" className="scroll-mt-6">
        <header className="mb-8 text-center">
          <h1 className="mb-3 bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-4xl font-bold text-transparent sm:text-5xl">
            Plans & billing
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            Choose Free or Premium, or change your plan whenever you like.
            Updates apply through Clerk Billing.
          </p>
        </header>
        <div className="mx-auto max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <PricingTable />
        </div>
      </section>
    </div>
  );
}
