"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

export type MarkdownSection = {
  section_id: string;
  heading: string;
  markdown: string;
};

type PipelineMarkdownPanelProps = {
  sections: MarkdownSection[];
  emptyMessage: string;
  streaming?: boolean;
};

export function PipelineMarkdownPanel({
  sections,
  emptyMessage,
  streaming = false,
}: PipelineMarkdownPanelProps) {
  if (sections.length === 0) {
    return (
      <p className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        {streaming ? "Waiting for output…" : emptyMessage}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3">
      {sections.map((s) => (
        <details
          key={s.section_id}
          className="group rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-950"
        >
          <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-gray-900 marker:content-none dark:text-gray-100 [&::-webkit-details-marker]:hidden">
            <span className="inline-flex w-full items-center justify-between gap-2">
              <span>{s.heading}</span>
              <span className="text-xs font-normal text-gray-500 group-open:hidden dark:text-gray-400">
                Show
              </span>
              <span className="hidden text-xs font-normal text-gray-500 group-open:inline dark:text-gray-400">
                Hide
              </span>
            </span>
          </summary>
          <div className="markdown-content prose prose-sm prose-neutral max-w-none border-t border-gray-100 px-4 py-3 dark:border-gray-800 dark:prose-invert">
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
              {s.markdown}
            </ReactMarkdown>
          </div>
        </details>
      ))}
    </div>
  );
}
