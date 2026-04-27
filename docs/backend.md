# Backend — Technical Reference

**Stack:** FastAPI · Python 3.11+ · SQLAlchemy (async) · SQLite (dev) → Postgres (prod) · OpenAI GPT-4o  

---

## Table of Contents

1. [How to Run Locally](#1-how-to-run-locally)
2. [Project Structure](#2-project-structure)
3. [API Reference](#3-api-reference)
4. [SSE Stream Format](#4-sse-stream-format)
5. [Database Schema](#5-database-schema)
6. [AI Agent Pipeline](#6-ai-agent-pipeline)
7. [Integration Guide](#7-integration-guide)
8. [Observability (Langfuse)](#8-observability-langfuse)
9. [Environment Variables](#9-environment-variables)
10. [Golden-case evals & GitHub Actions](#10-golden-case-evals--github-actions)

---

## 1. How to Run Locally

```bash
cd backend

# Run the automated test suite (no API key needed, ~1 second)
uv run pytest tests/ -v

# Start the live development server
uv run uvicorn src.main:app --reload --port 8000
```

Make sure `backend/.env` contains your OpenAI API key before starting the server:
```
OPENAI_API_KEY=sk-...
```

Golden-case eval jobs in GitHub Actions are documented in **[§10](#10-golden-case-evals--github-actions)** (same content as **`docs/PROJECT_WALKTHROUGH.md`** §22).

Delete `backend/litigation.db` if you get a database error on first run — the schema may have changed.

### Smoke test with curl

`POST /api/v1/analyze` is **`multipart/form-data`** (same as the Next.js client in `frontend/src/lib/api.ts`), not JSON.

```bash
# Health check
curl http://localhost:8000/health

# Who am I — in non-production, omitting Bearer falls back to X-User-Id (see dependencies.py)
curl http://localhost:8000/api/v1/me -H "X-User-Id: alice"

# Run an analysis (streams SSE) — title is required; case_text and/or file body must yield text
curl -N -X POST http://localhost:8000/api/v1/analyze \
  -H "X-User-Id: alice" \
  -F "title=Contract dispute" \
  -F "case_text=On 1 Jan 2024, John signed a contract with ABC Ltd for delivery of goods worth KES 200,000. ABC failed to deliver. John seeks damages."

# List past cases
curl "http://localhost:8000/api/v1/cases" -H "X-User-Id: alice"

# Case detail (paste case_id from the final {"type":"complete",...} event)
curl "http://localhost:8000/api/v1/cases/<case_id>" -H "X-User-Id: alice"
```

> **Note:** Earlier JSON `raw_case_text` examples and mixed header casing referenced by a previous archived doc version are not linked here because the archive file is not present in this repository.

---

## 2. Project Structure

```
backend/
├── main.py              # entry point shim: from src.main import app
├── src/
│   ├── main.py          # FastAPI app, CORS, request logging middleware, routers, lifespan
│   ├── cli.py           # dev server launcher
│   ├── core/
│   │   ├── config.py       # pydantic-settings
│   │   ├── logging.py      # structlog
│   │   ├── openai_client.py
│   │   └── security.py     # Clerk JWKS JWT validation
│   ├── database/
│   │   ├── models.py    # ORM table definitions: User, Case, AgentStep
│   │   └── session.py   # engine, session factory, get_db, init_db
│   ├── schemas/
│   │   ├── ai_schemas.py   # Pydantic shapes for AI agent inputs/outputs
│   │   └── api_schemas.py  # Pydantic shapes for HTTP requests/responses
│   ├── agents/
│   │   ├── extraction.py   # GPT-4o-mini: extract facts, entities, timeline
│   │   ├── strategy.py     # GPT-4o: map facts to Kenyan law + arguments
│   │   ├── drafting.py     # GPT-4o: produce formal markdown brief
│   │   ├── qa.py           # GPT-4o-mini: hallucination + logic audit
│   │   └── orchestrator.py # runs all 5 steps, streams SSE, saves to DB
│   ├── api/
│   │   ├── dependencies.py  # get_current_user — Clerk JWT + dev X-User-Id fallback
│   │   ├── routes_analyze.py
│   │   ├── routes_auth.py
│   │   └── routes_cases.py
│   └── rag/
│       ├── retriever.py     # embed + Chroma similarity search
│       ├── vector_store.py
│       └── ingestion.py
└── tests/
    ├── conftest.py          # fixtures, mock agent data, helpers
    ├── test_analyze.py      # 45 tests — analyze SSE, validation, DELETE, etc.
    ├── test_history.py      # 26 tests — listing, isolation, detail
    ├── test_health.py       # 3 tests
    ├── test_me.py           # 5 tests
    ├── test_rag.py          # 38 tests — chunking, retriever, ingestion
    └── test_schemas.py      # 26 tests — Pydantic AI schemas
```

---

## 3. API Reference

### `GET /health`
Public. No auth required.
```json
{ "status": "ok" }
```

---

### `GET /api/v1/me`
Returns the authenticated user. **Production:** requires `Authorization: Bearer <Clerk JWT>` and `CLERK_JWKS_URL` configured. **Non-production:** if `Authorization` is omitted, **`X-User-Id`** is accepted as a dev/test shortcut (`src/api/dependencies.py`).

**Response:**
```json
{ "user_id": "alice", "email": null }
```

---

### `POST /api/v1/analyze`
Runs the full multi-agent pipeline. Returns **`text/event-stream`** (SSE).

**Content-Type:** `multipart/form-data`

**Form fields**

| Field | Required | Notes |
|-------|----------|--------|
| `title` | **Yes** | Non-blank string (max 255 chars after trim). |
| `case_text` | No | Optional typed narrative; may be empty if a file supplies text. |
| `case_file` | No | Optional `.txt`, `.md`, or `.pdf`; text is extracted and merged with `case_text`. |

At least one of **`case_text`** or **`case_file`** must yield non-empty merged text after strip/extract; otherwise **422** with a clear `detail` message.

**Auth headers:** same as `/me` (Bearer in prod; dev may use `X-User-Id` when `APP_ENV` is not `production`).

**Response:** SSE — see [SSE Stream Format](#4-sse-stream-format) below.

---

### `GET /api/v1/cases`
Returns all cases for the authenticated user, newest first.

**Response:**
```json
[
  {
    "id": "753fc3cb-17d0-4529-9aaf-2caa8dff611b",
    "title": "Contract dispute",
    "raw_input": "On 1 Jan 2024, John signed...",
    "status": "COMPLETED",
    "created_at": "2024-01-15T10:30:00+00:00"
  }
]
```

---

### `GET /api/v1/cases/{case_id}`
Returns a single case with all 5 agent step results.

Returns `404` if the case doesn't exist **or** belongs to a different user.

**Response:**
```json
{
  "id": "753fc3cb-...",
  "title": "Contract dispute",
  "raw_input": "On 1 Jan 2024...",
  "status": "COMPLETED",
  "created_at": "2024-01-15T10:30:00+00:00",
  "steps": [
    {
      "id": "...",
      "step_name": "extraction",
      "step_index": 0,
      "status": "COMPLETED",
      "result": { "core_facts": [...], "entities": [...], "chronological_timeline": [...] }
    },
    {
      "step_name": "rag_retrieval",
      "step_index": 1,
      "result": { "chunks": [] }
    },
    {
      "step_name": "strategy",
      "step_index": 2,
      "result": { "legal_issues": [...], "applicable_laws": [...], "arguments": [...], ... }
    },
    {
      "step_name": "drafting",
      "step_index": 3,
      "result": { "brief_markdown": "# IN THE MATTER OF...\n\n## FACTS\n..." }
    },
    {
      "step_name": "qa",
      "step_index": 4,
      "result": { "risk_level": "LOW", "hallucination_warnings": [], "missing_logic": [] }
    }
  ]
}
```

---

### `DELETE /api/v1/cases/{case_id}`

Deletes the case and its `agent_steps` for the authenticated user. Returns **404** if the case is missing or not owned by the caller.

---

## 4. SSE Stream Format

The `/api/v1/analyze` endpoint streams [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events): each message is a line `data: <json>` followed by a blank line (`\n\n`). The orchestrator (`src/agents/orchestrator.py`) **does not** emit legacy `step` / `running` / `completed` envelopes; it emits **rendered Markdown per section** plus terminal events.

> **Frontend note:** `EventSource` only supports GET. This API uses **POST + multipart**; the shipped client uses `fetch` + `ReadableStream` (`frontend/src/lib/api.ts`).

### `markdown_section` (one per completed pipeline stage)

After each agent step finishes, the client receives a chunk of Markdown suitable for appending to the live brief view:

```json
{
  "type": "markdown_section",
  "section_id": "extraction",
  "heading": "Fact extraction",
  "markdown": "## Facts\n\n- …"
}
```

`section_id` is one of: `extraction`, `rag_retrieval`, `strategy`, `drafting`, `qa`.

### `complete`

Emitted when the case row is marked **`COMPLETED`** (the brief is still delivered even if the QA step logged a warning and stored a failed step row in edge cases).

```json
{ "type": "complete", "case_id": "753fc3cb-17d0-4529-9aaf-2caa8dff611b" }
```

### `error`

Emitted on unrecoverable pipeline failure; `Case.status` becomes **`FAILED`**.

```json
{ "type": "error", "detail": "OpenAI rate limit exceeded" }
```

### Example sequence (happy path)

```
data: {"type":"markdown_section","section_id":"extraction","heading":"Fact extraction","markdown":"..."}

data: {"type":"markdown_section","section_id":"rag_retrieval","heading":"Precedent retrieval","markdown":"..."}

data: {"type":"markdown_section","section_id":"strategy","heading":"Legal strategy","markdown":"..."}

data: {"type":"markdown_section","section_id":"drafting","heading":"Draft brief","markdown":"..."}

data: {"type":"markdown_section","section_id":"qa","heading":"Quality review","markdown":"..."}

data: {"type":"complete","case_id":"753fc3cb-17d0-4529-9aaf-2caa8dff611b"}

```

<details>
<summary>Legacy SSE shape (superseded — kept for comparison)</summary>

Older documentation described per-step `running` / `completed` JSON with `data` payloads and a final `{ "step": "done", ... }` event. That does not match the current orchestrator; see [`docs/archive/backend.md.pre-audit-2026-04-21.md`](./archive/backend.md.pre-audit-2026-04-21.md) section 4.

</details>

---

## 5. Database Schema

Three tables. Status values are uppercase strings throughout.

### `users`
Populated by John when Clerk JWT auth is live.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Primary key |
| `clerk_id` | string | Unique, indexed |
| `email` | string | |
| `tier` | string | `"FREE"` or `"PRO"` |
| `created_at` | timestamp with tz | |

### `cases`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Primary key |
| `user_id` | string | Indexed. FK to `users.id` added by Sodiq when auth is live |
| `title` | string | Taken from the **`title`** form field on `POST /api/v1/analyze` (user-facing label / search) |
| `raw_input` | text | The full case text submitted by the user |
| `status` | string | `PROCESSING` → `COMPLETED` or `FAILED` |
| `created_at` | timestamp with tz | |

### `agent_steps`
One row per pipeline stage (`step_index` 0–4). A finished run has five rows; individual steps may be **`FAILED`** while the case still ends **`COMPLETED`** (RAG/QA non-critical paths in the orchestrator).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Primary key |
| `case_id` | UUID string | FK → `cases.id` |
| `step_name` | string | `extraction`, `rag_retrieval`, `strategy`, `drafting`, `qa` |
| `step_index` | int | `0` through `4` |
| `status` | string | `PROCESSING` → `COMPLETED` or `FAILED` |
| `result` | JSON | Structured agent output (or error metadata) for the step |

---

## 6. AI Agent Pipeline

Data flows sequentially. Each agent receives the output of all previous agents.

```
merged case text (case_text + optional file excerpt)
    │
    ▼
[0] Extraction  (gpt-4o-mini, temp=0.1)
    → core_facts: list[str]
    → entities: list[{name, type, role}]
    → chronological_timeline: list[{date, event}]
    │
    ▼
[1] RAG Retrieval  (Amit's ChromaDB — currently returns [])
    → chunks: list[str]  (relevant Kenyan statutes / case law excerpts)
    │
    ▼
[2] Strategy  (gpt-4o, temp=0.2)  ← receives extraction + rag chunks
    → legal_issues: list[str]
    → applicable_laws: list[str]
    → arguments: list[{issue, applicable_kenyan_law, argument_summary}]
    → counterarguments: list[str]
    → legal_reasoning: str
    │
    ▼
[3] Drafting  (gpt-4o, temp=0.3)  ← receives extraction + strategy
    → brief_markdown: str
      (sections: IN THE MATTER OF / FACTS / ISSUES / LEGAL ARGUMENTS / CONCLUSION)
    │
    ▼
[4] QA  (gpt-4o-mini, temp=0.1)  ← receives extraction + draft markdown
    → risk_level: "LOW" | "MEDIUM" | "HIGH"
    → hallucination_warnings: list[str]
    → missing_logic: list[str]
    → risk_notes: list[str]
```

### Prompt strategy

- **Extraction:** instructed to exclude emotional language, build strict chronological timeline, output valid JSON
- **Strategy:** instructed to cite specific Kenyan statutes (Law of Contract Act Cap 23, Land Act No. 6 of 2012, etc.)
- **Drafting:** instructed to produce formal Kenyan High Court language, output raw markdown (not JSON)
- **QA:** instructed to cross-reference draft against source facts, flag anything not grounded

---

## 7. Integration Guide

### Clerk JWT Auth

**Implemented** in `src/api/dependencies.py` + `src/core/security.py`:

- **Production (`APP_ENV=production`):** `Authorization: Bearer <Clerk JWT>` is required; `CLERK_JWKS_URL` must be set or the API returns **503** for auth misconfiguration.
- **Non-production:** if `Authorization` is **omitted**, the dependency accepts **`X-User-Id`** so curl and local tests work without live Clerk tokens.

Production frontends should send **Bearer** tokens (see `frontend/src/lib/api.ts` — add `Authorization` when Clerk session is wired for analyze/history calls).

---

### ChromaDB RAG

**Implemented** under `src/rag/` (`retriever.py`, `vector_store.py`, `ingestion.py`). Run `uv run python -m src.rag.ingestion` to build `data/vector_db/` from `data/raw/`. Tests patch retrieval where needed; see `tests/test_rag.py`.

---

### Postgres + Alembic

**`asyncpg`** is already listed in `pyproject.toml`. Set `DATABASE_URL=postgresql+asyncpg://...` in production.

Schema is still created via `init_db()` / `create_all` in development; for production evolution, add **Alembic** migrations when the team is ready (see archive doc for a starter command sequence).

---

### Frontend — analyze + SSE

The shipped client uses **`FormData`** + **`fetch`** + a **`ReadableStream`** reader (not `EventSource`). See **`frontend/src/lib/api.ts`** — `postAnalyzeStream`.

**SSE payload types** (parse each `data:` JSON line):

| `type` | Fields | UI action |
|--------|--------|-----------|
| `markdown_section` | `section_id`, `heading`, `markdown` | Append/render Markdown for that section. |
| `complete` | `case_id` | Navigate to `/dashboard/scans/{case_id}` (or your detail route). |
| `error` | `detail` | Show error toast / inline message. |

**REST history:** list/detail responses include `title`, `raw_input`, `status`, `created_at`, and embedded `steps[].result` JSON (structured agent outputs — not the SSE Markdown strings).

**Key field locations:**
| What | Where |
|------|-------|
| Brief markdown | `data.data.brief_markdown` on the `drafting` completed event |
| Risk level | `data.data.risk_level` on the `qa` completed event (`"LOW"`, `"MEDIUM"`, `"HIGH"`) |
| Hallucination warnings | `data.data.hallucination_warnings` on the `qa` completed event (array of strings) |
| Case ID after completion | `data.case_id` on the `done` event |
| History case text | `raw_input` field (not `case_text`) on `/api/v1/cases` response |

**CORS:** if you hit a CORS error, add your Cloud Run frontend URL to `allowed_origins` in `src/core/config.py`, or set the `ALLOWED_ORIGINS` env var in the backend Cloud Run service (via Terraform variable or GCP Secret Manager).

---

## 8. Observability (Langfuse)

All LLM calls (chat completions and embeddings across all 5 agents and the RAG retriever) are instrumented with [Langfuse](https://langfuse.com) for tracing, token counting, cost tracking, and eval scoring.

### How it works

`src/core/openai_client.py` is the single client factory used by every agent. When Langfuse keys are present it swaps in `langfuse.openai.AsyncOpenAI` — a drop-in wrapper that intercepts every OpenAI call and ships a trace to Langfuse cloud. No changes are needed in agent code.

Tracing is **opt-in**: if `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are blank, the factory falls back to the plain `openai.AsyncOpenAI` client.

### Setup

**Local (dev):** add to `backend/.env`:

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Production:** keys are stored in GCP Secret Manager and injected into Cloud Run at runtime via `terraform/backend/main.tf`. Fill them in `terraform/backend/terraform.tfvars` and run `terraform apply`.

Get your keys from the [Langfuse cloud dashboard](https://cloud.langfuse.com) → Project Settings → API Keys.

### What you see in the dashboard

| Signal | Details |
|--------|---------|
| Traces | One trace per pipeline run, with child spans per agent step |
| Latency | Per-agent and end-to-end wall-clock time |
| Token usage | Prompt + completion tokens per call |
| Cost | Estimated USD cost per run |
| Evals | LLM-as-judge scores can be attached via the Langfuse SDK or UI |

---

## 9. Environment Variables

All read from `backend/.env`. Copy **`backend/.env.example`** as a starting point (it documents Clerk, providers, and CORS).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | One of OpenAI / OpenRouter | `""` | Primary provider key when set |
| `OPENROUTER_API_KEY` | Optional alt | `""` | Used when OpenAI key unset (see `.env.example`) |
| `MODEL` | No | `gpt-4o` | Chat model id for agents (`settings.model`) |
| `DATABASE_URL` | No | SQLite URL in `.env.example` | Postgres in production |
| `CLERK_JWKS_URL` | Yes in prod with Clerk | `""` | JWKS URL for JWT verification |
| `CLERK_ISSUER` | Optional | — | Reserved in `.env.example` for stricter JWT checks if you extend `security.py` |
| `ALLOWED_ORIGINS` | No | `["http://localhost:3000"]` | JSON array of allowed CORS origins |
| `APP_ENV` | No | `development` | `production` enables JSON structlog output |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `AGENT_STEP_TIMEOUT_SECONDS` | No | `120` | Wall-clock timeout per agent step |
| `LANGFUSE_PUBLIC_KEY` | No | `""` | Langfuse public key — enables LLM tracing when set |
| `LANGFUSE_SECRET_KEY` | No | `""` | Langfuse secret key |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse instance URL |

---

## 10. Golden-case evals & GitHub Actions

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). See **`docs/PROJECT_WALKTHROUGH.md`** §22 for tables and rubric mapping.

```bash
cd backend
uv run python -m evals.eval_extraction
uv run python -m evals.eval_llm_judge
```
