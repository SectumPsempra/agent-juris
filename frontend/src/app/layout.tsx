import React from "react";
import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Geist, Geist_Mono } from "next/font/google";

import { AuthenticatedLayout } from "@/components/authenticated-layout";
import { PlatformHeader } from "@/components/platform-header";

import "../styles/globals.css";
import "react-datepicker/dist/react-datepicker.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Litigation Prep Assistant",
  description: "AI-powered litigation preparation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ClerkProvider>
          <div className="flex min-h-svh flex-col">
            <div className="flex min-h-0 flex-1 flex-col">
              <AuthenticatedLayout>{children}</AuthenticatedLayout>
            </div>
          </div>
        </ClerkProvider>
      </body>
    </html>
  );
}
