import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PipelineMarkdownPanel, type MarkdownSection } from "../pipeline-markdown-panel";

const SECTIONS: MarkdownSection[] = [
  {
    section_id: "extraction",
    heading: "Fact extraction",
    markdown: "## Core facts\n- John signed the agreement",
  },
  {
    section_id: "strategy",
    heading: "Legal strategy",
    markdown: "## Legal issues\n- Contract validity",
  },
  {
    section_id: "drafting",
    heading: "Draft brief",
    markdown: "# IN THE MATTER OF\n## FACTS\nDetails here.",
  },
];

// ── Empty state ───────────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — empty state", () => {
  it("shows emptyMessage when sections is empty and not streaming", () => {
    render(<PipelineMarkdownPanel sections={[]} emptyMessage="No output yet." />);
    expect(screen.getByText("No output yet.")).toBeInTheDocument();
  });

  it("shows 'Waiting for output…' when sections is empty and streaming=true", () => {
    render(<PipelineMarkdownPanel sections={[]} emptyMessage="No output yet." streaming />);
    expect(screen.getByText("Waiting for output…")).toBeInTheDocument();
  });

  it("renders no <details> elements when sections is empty", () => {
    const { container } = render(
      <PipelineMarkdownPanel sections={[]} emptyMessage="Nothing here." />
    );
    expect(container.querySelectorAll("details")).toHaveLength(0);
  });
});

// ── Sections rendering ────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — sections rendering", () => {
  it("renders one <details> element per section", () => {
    const { container } = render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="" />);
    expect(container.querySelectorAll("details")).toHaveLength(3);
  });

  it("renders each section heading in a <summary>", () => {
    render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="" />);
    expect(screen.getByText("Fact extraction")).toBeInTheDocument();
    expect(screen.getByText("Legal strategy")).toBeInTheDocument();
    expect(screen.getByText("Draft brief")).toBeInTheDocument();
  });

  it("does not show emptyMessage when sections are present", () => {
    render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="Nothing here." />);
    expect(screen.queryByText("Nothing here.")).not.toBeInTheDocument();
  });
});

// ── Show / Hide toggle ────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — show/hide toggle", () => {
  it("<details> elements are closed by default", () => {
    const { container } = render(
      <PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />
    );
    const details = container.querySelector("details");
    expect(details).not.toHaveAttribute("open");
  });

  it("opens the <details> element after clicking the summary", async () => {
    const { container } = render(
      <PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />
    );
    await userEvent.click(screen.getByText("Fact extraction"));
    expect(container.querySelector("details")).toHaveAttribute("open");
  });

  it("closes the <details> element after clicking twice", async () => {
    const { container } = render(
      <PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />
    );
    await userEvent.click(screen.getByText("Fact extraction"));
    await userEvent.click(screen.getByText("Fact extraction"));
    expect(container.querySelector("details")).not.toHaveAttribute("open");
  });
});

// ── Markdown content ──────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — markdown content", () => {
  it("renders markdown text content inside the panel", () => {
    render(<PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />);
    expect(screen.getByText(/John signed the agreement/)).toBeInTheDocument();
  });

  it("renders a QA section with risk level text", () => {
    const qa: MarkdownSection[] = [
      { section_id: "qa", heading: "Quality review", markdown: "**Risk level:** `LOW`" },
    ];
    render(<PipelineMarkdownPanel sections={qa} emptyMessage="" />);
    expect(screen.getByText(/LOW/)).toBeInTheDocument();
  });

  it("renders all three sections' content into the DOM", () => {
    render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="" />);
    expect(screen.getByText(/John signed the agreement/)).toBeInTheDocument();
    expect(screen.getByText(/Contract validity/)).toBeInTheDocument();
    expect(screen.getByText(/Details here/)).toBeInTheDocument();
  });
});
