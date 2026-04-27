"use client";

import { useId } from "react";

/** Vector brand mark (brief + scales); transparent — tuned for dark sidebar chrome. */
export function LitigationPrepMark({ className }: { className?: string }) {
  const gid = useId().replace(/:/g, "");
  const gradId = `lpa-mark-gradient-${gid}`;
  const stroke = `url(#${gradId})`;

  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient
          id={gradId}
          x1="6"
          y1="42"
          x2="42"
          y2="6"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#38bdf8" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      <path
        d="M12 5h16.5L39 15.5V41a3 3 0 0 1-3 3H12a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3Z"
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M28.5 5V14H39"
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M24 35V21"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M15 21h18"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M15 21v4.5l-3 5.5h6l-3-5.5"
        stroke={stroke}
        strokeWidth="1.75"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <path
        d="M33 21v4.5l-3 5.5h6l-3-5.5"
        stroke={stroke}
        strokeWidth="1.75"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
