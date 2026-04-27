# Documentation audit log — 2026-04-21

This log records how **agent-juris** was checked against the **Capstone Rubric** (Excel: `Capstone Rubric.xlsx`), what ran locally, and where docs were corrected.

---

## Tools run (local)

| Command | Result |
|---------|--------|
| `cd backend && uv run pytest tests/ -q` | **143 passed** (~5 s) |
| `cd backend && uv run ruff check .` | **Clean** after `main.py` noqa for uvicorn re-export |
| `cd backend && uv run ruff format --check .` | **Clean** after `uv run ruff format .` (11 files were mis-formatted before this audit) |
| `cd backend && uv run mypy src --ignore-missing-imports` | Run as in CI (see workflow) |

CI — **`.github/workflows/backend-deploy.yml`:** runs `compileall`, **ruff** on `src` + `tests`, **mypy**, **pytest** with `--cov-fail-under=70`.

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). See **`docs/PROJECT_WALKTHROUGH.md`** §22 for tables and rubric mapping.

---

## Rubric cross-walk (Q1 Capstone Rubric.xlsx)

Scores below are **evidence-based** against the current repo (not the old `Rubric.md` text). Scale **0–5** per criterion in the spreadsheet.

### Technical Depth (~20% weight in spreadsheet)

| Criterion | Score | Evidence in repo |
|-----------|------:|------------------|
| Problem selection & scope | **4** | Kenyan litigation prep, multi-agent brief; README + walkthroughs state scope and trade-offs. |
| Architecture & design choices | **4** | FastAPI `src/` layout, SSE orchestrator, RAG module, Clerk + dev header auth, Postgres/SQLite; design table in root README. |
| Prompt & model interaction quality | **4** | Versioned prompts under `src/agents/prompts/`, **instructor** + Pydantic on structured agents, few-shot extraction. |
| Orchestration & control flow | **4** | Sequential pipeline, **tenacity** retries on transient OpenAI errors, **`asyncio.wait_for`** per step, RAG + QA non-critical paths with warnings in logs. |

### Engineering Practices (~20%)

| Criterion | Score | Evidence in repo |
|-----------|------:|------------------|
| Code quality | **4** | Modular packages, shared `openai_client`, Ruff + Mypy in CI, typed schemas. |
| Logging & error handling | **4** | **`structlog`** in `src/core/logging.py`; **`configure_logging()`** at startup; **`get_logger`** in orchestrator + agents + `dependencies.py`; HTTP middleware logs requests; `logger.exception` on pipeline failure; global 500 handler logs unhandled errors. *Not* score-5: no Prometheus/tracing. |
| Unit / integration tests | **5** | **143** pytest tests, async client, mocks; coverage gate **70%** in CI. |
| Observability | **3** | Structured **structlog** + HTTP middleware timing; pipeline and **per-agent `llm_call_*`** events with model / duration / tokens in agent modules. Gaps vs rubric 5: no Prometheus `/metrics`, no tracing, no dashboards. |

### Production Readiness (~15%)

| Criterion | Score | Evidence |
|-----------|------:|-----------|
| Solution feasibility | **4** | Docker/infra, Clerk path, RAG ingestion, working SSE; real deployment still env-specific. |
| Evaluation strategy | **4** | **`evals.yml`**: golden **`eval_extraction`** in CI on relevant **`main`** pushes (non-blocking via **`continue-on-error`** until **`OPENAI_API_KEY`** is set and flag removed); expensive **`eval_llm_judge`** manual-only. |
| Deployment | **4** | GHA backend workflow runs lint + types + tests + coverage; Dockerfile/infra present; full IaC/zero-downtime not claimed. |

### Presentation (spreadsheet section)

Not scored here (requires demo/video); UI exists in Next.js under `frontend/src/`.

---

## Documentation fixes applied

| Document | Issue | Resolution |
|----------|--------|------------|
| `backend/README.md` | Called project a “scaffold”, `/me` path, `app/core`, env “not wired” | Rewrote to match **`src/`** tree, **`/api/v1/*`**, Clerk + `.env`; pre-audit copy in **`docs/archive/`**. |
| `docs/backend.md` | `POST /analyze` shown as JSON + old SSE (`step`/`done`/`event`) | Updated to **multipart/form-data** (`title`, `case_text`, optional `case_file`), SSE **`type: markdown_section \| complete \| error`**; Clerk + dev `X-User-Id`; archive copy. |
| `Rubric.md` | Claimed no logging, wrong CI/tests | Replaced with current rubric table; old file archived. |
| `backend/Backend_walkthrough.md` | “56 passed”, JSON analyze, legacy SSE narrative | Updated to **143** tests, **multipart** curl, **`markdown_section`** SSE, current auth/RAG descriptions. |
| `docs/PROJECT_WALKTHROUGH.md` (2026-04-22) | Stale pytest banner, `EventSource` wording, rubric rows, tests tree | Banner + **143** counts, **`fetch`** SSE note, rubric tweaks, expanded `tests/`; archive: `docs/archive/PROJECT_WALKTHROUGH.md.pre-audit-2026-04-22.md`. |
| `docs/rag_integration_guide.md` (2026-04-22) | `rag-basic`, four agents, auth stub, old extraction, 133 tests | **`main`** scope, five stages, **instructor**, **Clerk JWKS**, **143** tests, Chroma retriever + corpus; archive: `rag_integration_guide.md.pre-audit-2026-04-22.md`. |
| `docs/rag_enrichments_evals_guide.md` (2026-04-22) | “8 new cases” only | **11** golden cases documented; archive: `rag_enrichments_evals_guide.md.pre-audit-2026-04-22.md`. |
| **`evals.yml` + docs** (2026-04-23) | Docs said evals not in CI / 3 golden cases only | **`Rubric.md`**, **`DOCUMENTATION_AUDIT_LOG.md`**, **`docs/PROJECT_WALKTHROUGH.md` §18/§22/§23**, **`docs/rag_enrichments_evals_guide.md`**, **`docs/rag_integration_guide.md` §7.5**, **`docs/backend.md`** (TOC **§9** + body), **`backend/README.md`**, **`backend/Backend_walkthrough.md`**, **`frontend/README.md`** one-liner, root **`README.md`** — canonical **`evals.yml`** blurb + **11** golden cases, optional hard gate. |
| `backend/main.py` | Ruff **F401** on `app` import | **`# noqa: F401`** — intentional re-export for `uvicorn main:app`. |

---

## Suggested next steps (rubric → higher scores)

1. **Observability (2 → 4):** optional `/metrics` or token usage fields on every `llm_call_*` log line.  
2. **Eval gate (optional):** set **`OPENAI_API_KEY`** and remove **`continue-on-error: true`** on **`extraction-eval`** in **`evals.yml`** if merges should fail on golden-case regression.  
3. **Ruff scope:** extend CI to `ruff check .` including `main.py` (already clean with noqa).
