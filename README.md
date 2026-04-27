# Litigation Prep Assistant

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Clerk](https://img.shields.io/badge/Clerk-Auth%20%26%20Billing-6C47FF?logo=clerk&logoColor=white)](https://clerk.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-E85D04?logo=databricks&logoColor=white)](https://www.trychroma.com)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-supported-8B5CF6)](https://openrouter.ai)
[![Tests](https://img.shields.io/badge/tests-143%20passing-22C55E?logo=pytest&logoColor=white)](./backend/tests)
[![Backend CI](https://github.com/Sectumpsempra/agent-juris/actions/workflows/backend-deploy.yml/badge.svg)](https://github.com/Sectumpsempra/agent-juris/actions/workflows/backend-deploy.yml)
[![Frontend CI](https://github.com/Sectumpsempra/agent-juris/actions/workflows/frontend-deploy.yml/badge.svg)](https://github.com/Sectumpsempra/agent-juris/actions/workflows/frontend-deploy.yml)
[![Cloud Run](https://img.shields.io/badge/Frontend-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![Cloud Run](https://img.shields.io/badge/Backend-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)

> **AI-powered litigation preparation for Kenyan law firms and paralegals.**

Litigation Prep Assistant is a multi-agent AI system that transforms raw case input -- text descriptions or uploaded PDFs -- into a structured legal brief. Four sequential agents (Extraction -> Strategy -> Drafting -> QA) process the case and stream their outputs step-by-step to the UI in real time via Server-Sent Events (SSE), giving lawyers and paralegals an interactive, auditable view of the AI's reasoning.

---

## Architecture

```mermaid
flowchart TB
    classDef frontend fill:#000000,stroke:#333,stroke-width:2px,color:#fff
    classDef backend fill:#026e3f,stroke:#333,stroke-width:2px,color:#fff
    classDef external fill:#f39c12,stroke:#333,stroke-width:2px,color:#fff
    classDef database fill:#2980b9,stroke:#333,stroke-width:2px,color:#fff
    classDef agent fill:#8e44ad,stroke:#333,stroke-width:2px,color:#fff
    classDef rag fill:#c0392b,stroke:#333,stroke-width:2px,color:#fff

    subgraph Client_Tier [Client & UI Tier]
        U((User / Lawyer))
        FE[Next.js App Router<br>GCP Cloud Run]:::frontend
    end

    subgraph External_Services[Identity & Billing]
        Clerk[Clerk Auth & Billing UI]:::external
    end

    subgraph Backend_Tier [Backend Application Tier - FastAPI on GCP Cloud Run]
        API_GW[FastAPI REST / API Router]:::backend
        Auth_MW[Clerk JWT Middleware]:::backend
        SSE[SSE Streamer<br>Step-by-step updates]:::backend

        API_GW --> Auth_MW
        Auth_MW --> SSE
    end

    subgraph AI_Pipeline[AI Multi-Agent Orchestration]
        Orchestrator[Async Pipeline / Orchestrator]:::agent
        A1[1. Extraction Agent<br>Facts, Entities, Timeline]:::agent
        A2[2. Strategy Agent<br>Legal Mapping + RAG]:::agent
        A3[3. Drafting Agent<br>Structured Brief]:::agent
        A4[4. QA Agent<br>Risk & Hallucination Check]:::agent

        Orchestrator --> A1
        A1 --> A2
        A2 --> A3
        A3 --> A4
        A4 --> Orchestrator
    end

    subgraph Data_Tier[Data & RAG Storage]
        DB[(PostgreSQL<br>Users, Cases, History)]:::database
        VD[(ChromaDB<br>Vector Store)]:::database
        RAG_Retriever[RAG Retrieval Layer<br>Kenyan Law Context]:::rag
    end

    subgraph LLM_Tier [External Intelligence]
        LLM[OpenAI / OpenRouter]:::external
    end

    U -->|Uploads PDF / Enters Text| FE
    FE <-->|Authenticates / Paywall| Clerk
    FE -->|POST /analyze| API_GW
    FE -.->|Listens to SSE stream| SSE

    API_GW <-->|Reads/Writes| DB
    Auth_MW <-->|Validates JWT| Clerk
    API_GW -->|Triggers| Orchestrator
    Orchestrator -.->|Yields Status| SSE

    A2 <-->|Queries for precedents| RAG_Retriever
    RAG_Retriever <-->|Fetches Embeddings| VD

    A1 & A2 & A3 & A4 <-->|Prompts & Completions| LLM
```

The backend orchestrates four agents sequentially. As each agent completes, the FastAPI `StreamingResponse` yields a `markdown_section` SSE event containing the rendered Markdown for that step. A final `complete` event carrying the `case_id` signals the end of the stream. The Next.js frontend consumes the stream and renders each section live -- no polling, no page reloads.

---

## Agent Roles

| Agent | Responsibility |
|-------|---------------|
| **Extraction Agent** | Pulls facts, named entities, and a chronological timeline from the raw case input using few-shot prompting and instructor-validated structured output |
| **Strategy Agent** | Retrieves relevant Kenyan statute excerpts via ChromaDB RAG, then maps facts to legal issues, arguments, and counterarguments |
| **Drafting Agent** | Produces a formal litigation brief following Kenyan High Court drafting conventions: Facts, Issues, Arguments, Counterarguments, Conclusion |
| **QA Agent** | Audits the draft for hallucinations, fabricated statute citations, logical gaps, and internal contradictions; assigns a risk level |

---

## Features

- **Deterministic pipeline** -- not a chatbot; a fixed Extraction -> Strategy -> Drafting -> QA sequence with a clear start and a typed output at every step
- **Structured output with automatic retry** -- instructor enforces Pydantic schemas on every JSON-mode LLM call; malformed responses are retried transparently without crashing the pipeline
- **Kenyan law RAG** -- ChromaDB with OpenAI `text-embedding-3-small` embeddings grounds strategy arguments in real statutes and precedents before reasoning begins
- **Few-shot extraction prompts** -- the extraction agent uses a versioned prompt registry with a domain-specific example to anchor output quality across model updates
- **Resilient orchestration** -- tenacity retries transient OpenAI errors with exponential backoff; each step has a configurable wall-clock timeout; RAG and QA failures degrade gracefully without discarding the brief
- **Real-time step viewer** -- SSE stream lets the UI render each agent section as it completes, giving the user live feedback on a process that would otherwise feel like a black box
- **Structured JSON logging** -- structlog emits per-request HTTP logs and per-LLM-call telemetry (latency, prompt tokens, completion tokens) in newline-delimited JSON in production
- **Offline evaluation harness** -- golden test cases for schema regression and an LLM-as-judge script that scores pipeline output on completeness, factual grounding, and actionability
- **Provider flexibility** -- `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are supported; OpenAI takes priority when both are set, so switching providers requires only an env change
- **Auth & billing** -- Clerk handles sign-in, route protection, and subscription gating; JWKS validation runs server-side with a 5-minute cache
- **History** -- every analysis is persisted in the database with all five agent step results attached, retrievable from the dashboard
- **Monorepo** -- frontend, backend, infra, data, and docs live in one repo with clean domain boundaries

---

## Repository Layout

```
agent-juris/
│
├── .github/workflows/
│   ├── backend-deploy.yml      # pytest + ruff + mypy + coverage gate
│   └── frontend-deploy.yml     # lint + Next.js build
│
├── frontend/                   # Next.js 16 App Router
│   └── src/
│       ├── app/
│       │   ├── page.tsx                    # / landing (redirects signed-in users)
│       │   ├── dashboard/
│       │   │   ├── page.tsx                # /dashboard overview
│       │   │   ├── new-scan/page.tsx       # /dashboard/new-scan — run a new analysis
│       │   │   └── scans/
│       │   │       ├── page.tsx            # /dashboard/scans — history list
│       │   │       └── [id]/page.tsx       # /dashboard/scans/[id] — analysis detail
│       │   ├── public/                     # /public/login, /public/pricing (unauthenticated)
│       │   └── subscriptions/page.tsx
│       ├── components/
│       │   ├── ui/                         # shadcn/ui primitives
│       │   ├── forms/case-input-form.tsx
│       │   ├── dashboard/                  # HistoryTable, FileUploader
│       │   ├── agents/                     # AgentStepViewer, ResultPanel
│       │   └── pipeline-markdown-panel.tsx # SSE stream renderer
│       ├── lib/
│       │   ├── api.ts                      # fetch + SSE client
│       │   └── agent-step-markdown.ts      # step -> Markdown serializer
│       └── types/case.ts
│
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── orchestrator.py             # async pipeline generator + SSE yield
│   │   │   ├── extraction.py               # few-shot + instructor JSON mode
│   │   │   ├── strategy.py                 # RAG-augmented legal analysis
│   │   │   ├── drafting.py                 # High Court brief in Markdown
│   │   │   ├── qa.py                       # hallucination + logic audit
│   │   │   ├── format_markdown.py          # agent output -> Markdown body
│   │   │   └── prompts/                    # versioned prompt modules
│   │   ├── api/
│   │   │   ├── dependencies.py             # Clerk JWT auth dependency
│   │   │   ├── routes_analyze.py           # POST /analyze -> SSE StreamingResponse
│   │   │   ├── routes_cases.py             # GET/DELETE /cases, GET /cases/{id}
│   │   │   └── routes_auth.py              # GET /me
│   │   ├── core/
│   │   │   ├── config.py                   # pydantic-settings: env -> typed config
│   │   │   ├── logging.py                  # structlog setup (JSON prod / console dev)
│   │   │   ├── openai_client.py            # shared AsyncOpenAI singleton (OpenAI / OpenRouter)
│   │   │   └── security.py                 # Clerk JWKS validation with TTL cache
│   │   ├── database/                       # SQLAlchemy async models + session
│   │   ├── rag/
│   │   │   ├── ingestion.py                # chunk + embed + write to ChromaDB
│   │   │   ├── retriever.py                # embed query + cosine similarity search
│   │   │   └── vector_store.py             # ChromaDB client + collection factory
│   │   ├── schemas/                        # AI output schemas, API request/response schemas
│   │   ├── serializers/                    # DB model -> API schema adapters
│   │   └── services/case_file_text.py      # PDF/TXT extraction from uploaded files
│   ├── evals/
│   │   ├── golden_cases.json               # 11 golden scenarios with expected output constraints
│   │   ├── eval_extraction.py              # schema regression: runs agent, checks constraints
│   │   └── eval_llm_judge.py               # GPT-4o scores full pipeline on 3 rubric dimensions
│   └── tests/
│       ├── conftest.py                     # shared fixtures, mock agent outputs, SSE helpers
│       ├── test_analyze.py                 # SSE pipeline, input validation, error handling, DELETE
│       ├── test_history.py                 # case listing, user isolation, step detail
│       ├── test_rag.py                     # chunk_text, rag_retrieve, ingest_documents, integration
│       ├── test_schemas.py                 # AI Pydantic schema unit tests
│       ├── test_health.py
│       └── test_me.py
│
├── data/
│   ├── raw/                                # Kenyan statute source files (txt)
│   │   ├── contract_act_cap_23.txt
│   │   ├── employment_act_2007.txt
│   │   └── land_act_2012.txt
│   ├── test_cases/                         # Sample cases for manual testing
│   ├── processed/                          # Cleaned JSONL chunks (generated)
│   └── vector_db/                          # ChromaDB persistent index (git-ignored)
│
├── infra/
│   ├── docker-compose.yml                  # Postgres for local dev
│   ├── Dockerfile.backend                  # Container image for Render
│   └── init.sql
│
└── docs/
    ├── backend.md                          # Backend API reference and integration notes
    └── rag_integration_guide.md            # RAG pipeline design, ingestion, retrieval walkthrough
```

---

## Prerequisites

| Layer | Requirement |
|-------|-------------|
| Backend | Python 3.11+ and [uv](https://docs.astral.sh/uv/) |
| Frontend | Node.js 20+ LTS and npm |
| Local DB | Docker + Docker Compose (for Postgres; SQLite works with no setup) |
| Auth | A [Clerk](https://clerk.com) application (free tier sufficient) |
| LLM | An OpenAI API key, or an OpenRouter API key |

---

## Quick Start

### 1. Clone and configure environment variables

```bash
git clone https://github.com/<your-org>/agent-juris.git
cd agent-juris
```

Copy the example env files and fill in your keys:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

**`backend/.env` (minimum required):**

```dotenv
# Use OpenAI directly, or replace with OPENROUTER_API_KEY for OpenRouter.
OPENAI_API_KEY=sk-...
# SQLite requires no extra setup; swap for Postgres when needed.
DATABASE_URL=sqlite+aiosqlite:///./litigation.db
```

**`frontend/.env.local` (minimum required):**

```dotenv
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 2. Start the local database (optional -- skip if using SQLite)

```bash
cd infra
docker compose up -d
```

### 3. Run the API

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API docs: `http://127.0.0.1:8000/docs`

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000`

### 5. Build the RAG vector store (first time only)

```bash
cd backend
uv run python -m src.rag.ingestion
```

This reads all `.txt` and `.md` files from `data/raw/`, chunks them, embeds with `text-embedding-3-small`, and writes the index to `data/vector_db/`. Re-run whenever you add documents. See [docs/rag_integration_guide.md](./docs/rag_integration_guide.md) for a full walkthrough.

---

## Testing

### Backend

The backend test suite uses `pytest` with async support. All agents, the LLM, and the database are mocked -- tests run in under 20 seconds with zero API cost.

```bash
cd backend
uv run pytest             # run all 143 tests
uv run pytest -v          # verbose -- show each test name
uv run pytest -x          # stop on first failure
uv run pytest --tb=short  # concise failure tracebacks
```

**Test coverage by file:**

| File | What it covers |
|------|---------------|
| `tests/test_health.py` | `GET /health` liveness check |
| `tests/test_me.py` | `GET /api/v1/me` user identity endpoint |
| `tests/test_analyze.py` | `POST /api/v1/analyze` -- SSE pipeline, input validation, section ordering, error handling, per-agent DB persistence, `DELETE /api/v1/cases/{id}` |
| `tests/test_history.py` | `GET /api/v1/cases` + `GET /api/v1/cases/{id}` -- history listing, user isolation, step detail retrieval |
| `tests/test_rag.py` | `chunk_text` unit tests, `rag_retrieve` mocked retrieval, `ingest_documents` mocked embedding + Chroma, pipeline integration |
| `tests/test_schemas.py` | AI Pydantic schema unit tests -- model validation and serialization |

Run with coverage:

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Evaluations (live API calls, incurs cost)

Two eval scripts live in `backend/evals/` (they exit **0** on pass, **1** on failure):

```bash
# Golden-case extraction checks — runs every case in golden_cases.json (11 scenarios)
uv run python -m evals.eval_extraction

# LLM-as-judge — full pipeline + GPT-4o scores per case (~$0.30+ for all cases; run sparingly)
uv run python -m evals.eval_llm_judge
uv run python -m evals.eval_llm_judge --threshold 3.5   # stricter pass threshold
```

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). See **`docs/PROJECT_WALKTHROUGH.md`** §22 for tables and rubric mapping.

---

## Observability

### Structured logging

All backend logging uses [structlog](https://www.structlog.org/). In development the output is human-readable console output. In production (`APP_ENV=production`) it switches to newline-delimited JSON suitable for any log aggregator (Datadog, Loki, CloudWatch, etc.).

Every request logs at `INFO` level with `method`, `path`, `status_code`, and `duration_ms`. Every LLM call logs:

| Field | Example value | What it tells you |
|-------|--------------|-------------------|
| `event` | `"llm_call_complete"` | Log event type |
| `model` | `"gpt-4o"` | Model used |
| `agent` | `"extraction"` | Which agent made the call |
| `duration_ms` | `1842` | Wall-clock latency for the API call |
| `prompt_tokens` | `1103` | Input tokens consumed |
| `completion_tokens` | `412` | Output tokens consumed |
| `case_id` | `"a3f1..."` | Correlates all logs for one pipeline run |

### Querying logs locally

With the default console renderer, filter by keyword:

```bash
uv run uvicorn src.main:app --reload 2>&1 | grep llm_call_complete
```

In production (JSON mode), pipe through `jq`:

```bash
# All LLM calls for a specific case
journalctl -u litigation-prep | jq 'select(.case_id == "a3f1...")'

# Average latency per agent across a log file
cat app.log | jq -r 'select(.event == "llm_call_complete") | [.agent, .duration_ms] | @tsv' \
  | awk '{sum[$1]+=$2; n[$1]++} END {for (a in sum) print a, sum[a]/n[a]}'
```

### Log levels

| Level | When used |
|-------|-----------|
| `INFO` | Request lifecycle, each pipeline step completing, LLM call telemetry |
| `WARNING` | Non-critical step failures (RAG retrieval failure, QA step failure) — pipeline continues |
| `ERROR` / `EXCEPTION` | Critical step failures that abort the pipeline and mark the case `FAILED` |

### What is not yet instrumented

- No distributed tracing (no OpenTelemetry spans) — log correlation is via `case_id` only
- No metrics endpoint (no Prometheus `/metrics`) — latency and token data lives in logs
- No alerting — add a log-based alert on `pipeline_failed` events in your aggregator

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | - | System health check |
| `GET` | `/api/v1/me` | Clerk JWT | Returns authenticated user profile |
| `POST` | `/api/v1/analyze` | Clerk JWT | Multipart form (`title`, `case_text`, optional `case_file`); returns SSE stream |
| `GET` | `/api/v1/cases` | Clerk JWT | Lists all past analyses for the user (optional `?q=` title filter) |
| `GET` | `/api/v1/cases/{id}` | Clerk JWT | Returns full case result and all agent steps |
| `DELETE` | `/api/v1/cases/{id}` | Clerk JWT | Deletes a case and its agent steps |

### SSE stream format (`POST /api/v1/analyze`)

Each line has the form `data: <json>\n\n`. Three event types are emitted:

```json
{ "type": "markdown_section", "section_id": "extraction",    "heading": "Fact extraction",    "markdown": "..." }
{ "type": "markdown_section", "section_id": "rag_retrieval", "heading": "Precedent retrieval", "markdown": "..." }
{ "type": "markdown_section", "section_id": "strategy",      "heading": "Legal strategy",      "markdown": "..." }
{ "type": "markdown_section", "section_id": "drafting",      "heading": "Draft brief",         "markdown": "..." }
{ "type": "markdown_section", "section_id": "qa",            "heading": "Quality review",      "markdown": "..." }
{ "type": "complete", "case_id": "<uuid>" }
{ "type": "error",    "detail": "<message>" }
```

---

## Deployment

| Service | Platform | Notes |
|---------|----------|-------|
| Frontend | [GCP Cloud Run](https://cloud.google.com/run) | Image built from `frontend/Dockerfile` and pushed to Artifact Registry; provisioned via `terraform/frontend/` |
| Backend | [GCP Cloud Run](https://cloud.google.com/run) | Image built from `backend/Dockerfile` and pushed to Artifact Registry; provisioned via `terraform/backend/` |
| Database | [GCP Cloud SQL (PostgreSQL)](https://cloud.google.com/sql) (Postgres 15) | Provisioned via `terraform/database/`; `DATABASE_URL` stored in Secret Manager |
| Vector store | Packed into Docker image or mounted volume | See `data/vector_db/` -- add to `.dockerignore` carefully |

---

## API Costs

All LLM calls use OpenAI `gpt-4o` (or the equivalent model on OpenRouter). Embedding calls use `text-embedding-3-small`. The table below shows approximate token usage and cost per pipeline run based on a medium-length case description (~500 words input).

| Step | Model | Est. input tokens | Est. output tokens | Est. cost (USD) |
|------|-------|------------------:|-------------------:|----------------:|
| Extraction | gpt-4o | 1,100 | 450 | $0.007 |
| RAG embedding (query) | text-embedding-3-small | 120 | — | <$0.001 |
| Strategy | gpt-4o | 2,200 | 750 | $0.013 |
| Drafting | gpt-4o | 3,400 | 1,400 | $0.023 |
| QA | gpt-4o | 4,100 | 380 | $0.014 |
| **Total per run** | | **~10,920** | **~2,980** | **~$0.057** |

> Prices based on OpenAI public pricing as of Q2 2025: gpt-4o at $2.50/1M input tokens and $10.00/1M output tokens; text-embedding-3-small at $0.02/1M tokens. Actual costs vary with case length and model updates.

### Cost controls

- The extraction and strategy steps are the cheapest; the drafting step is the most expensive because it produces a long brief.
- To reduce cost during development, set a shorter `agent_step_timeout_seconds` in `.env` to fail fast, or mock agents in test runs (the test suite has zero API cost by design).
- Switching to `gpt-4o-mini` via `OPENROUTER_API_KEY` pointing at a cheaper model cuts cost by ~10× at the expense of brief quality.
- The LLM-as-judge eval (`eval_llm_judge.py`) runs the full pipeline plus a judge call per golden case (~**$0.30+** for all cases) — keep it **manual** in CI or run locally before releases.

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Frontend framework | Next.js 16 (App Router) |
| UI components | shadcn/ui + Tailwind CSS |
| Auth & billing | Clerk |
| Backend framework | FastAPI |
| Agent orchestration | Custom async pipeline with tenacity retry and step timeouts |
| LLM provider | OpenAI or OpenRouter (priority selection via env) |
| Structured output | Pydantic + instructor (JSON mode, automatic retry) |
| Embeddings + RAG | OpenAI `text-embedding-3-small` + ChromaDB (cosine similarity) |
| Logging | structlog (JSON in production, console in dev; LLM telemetry per call) |
| Relational database | PostgreSQL / SQLite (SQLAlchemy async) |
| Real-time streaming | Server-Sent Events (SSE) |
| Package manager (BE) | uv |
| CI/CD | GitHub Actions: backend lint/types/tests + coverage; optional **`evals.yml`** (golden extraction eval, non-blocking by default); frontend build |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| SSE over REST polling | FastAPI's `StreamingResponse` yields each step result as it completes, giving the UI a live feed without a long-polling loop or websocket management |
| Sequential async pipeline over multi-agent framework | Four agents with a fixed causal order do not need a routing framework; a plain async generator is easier to trace, test, and extend without framework lock-in |
| instructor (JSON mode) for structured output | Automatic Pydantic schema injection into the prompt and transparent retry on malformed JSON; removes manual `json.loads` and error handling from every agent |
| Few-shot extraction with versioned prompts | A single realistic Kenyan legal example in the extraction prompt significantly stabilises output structure; `PROMPT_VERSION` constants allow output quality to be correlated with prompt changes in logs |
| tenacity retry on OpenAI calls | Transient rate-limit and connection errors are retried with exponential backoff rather than surfaced to the user immediately, improving reliability without complexity |
| QA step treated as non-critical | A QA failure must not discard an otherwise complete brief; the pipeline emits a `complete` event and the QA section is simply absent, rather than aborting with an error |
| structlog for logging | Newline-delimited JSON in production is ingestible by any log aggregator without format negotiation; per-step LLM telemetry (latency, tokens) is emitted at `INFO` level |
| OpenAI / OpenRouter priority selection | The shared client factory checks `OPENAI_API_KEY` first, then `OPENROUTER_API_KEY`; no agent code changes are needed to switch providers |
| Clerk JWKS validation server-side | Bearer tokens are verified against Clerk's public JWKS with a 5-minute in-memory cache, avoiding a network round-trip on every request while still rotating keys within a reasonable window |
| SQLite in dev, Postgres (Cloud SQL) in prod | SQLAlchemy async supports both via `DATABASE_URL`; SQLite requires zero setup for local development and CI, while Cloud SQL handles concurrent production writes without locking issues |
| ChromaDB as the vector store | Embedded Python library with no separate process or infra to manage; the index is a directory on disk that travels with the Docker image; suitable for a corpus up to ~100K chunks before a hosted solution is warranted |
| 800-char chunks with 100-char overlap | A chunk must be large enough to contain a complete statutory sentence (~3–5 lines) but small enough that the top-k results fit in the strategy prompt context window; overlap prevents a relevant sentence from being split across two non-adjacent chunks |
| RAG retrieval before strategy (not before extraction) | Extraction works on raw facts and needs no legal context; RAG results are passed to strategy where statute grounding is needed to map facts to legal arguments; this avoids inflating the extraction prompt unnecessarily |
| `asyncio.wait_for` per step | A per-step wall-clock timeout (configurable via `AGENT_STEP_TIMEOUT_SECONDS`) prevents a single hung OpenAI call from stalling the entire SSE stream; the client sees an error event rather than a silent connection timeout |
| Versioned prompt modules | Each agent's system prompt is a module-level constant with a `PROMPT_VERSION` string; when a prompt is changed the version is bumped, so logs correlate output quality regressions with the exact prompt version that produced them |
| Pydantic `BaseSettings` for config | All environment variables are validated at startup with types and defaults; a missing required key raises a clear error before any agent code runs, rather than failing silently mid-pipeline |

---

## Documentation

- [backend/README.md](./backend/README.md) -- Python layout, dependencies, and local run instructions
- [frontend/README.md](./frontend/README.md) -- Next.js scripts, routing, and environment variables
- [docs/backend.md](./docs/backend.md) -- API reference, SSE format, integration notes
- [docs/rag_integration_guide.md](./docs/rag_integration_guide.md) -- RAG pipeline design, ingestion walkthrough, retrieval internals, and ChromaDB configuration
- [docs/DOCUMENTATION_AUDIT_LOG.md](./docs/DOCUMENTATION_AUDIT_LOG.md) -- Doc–code audit (2026-04-21): rubric mapping, pytest/Ruff results, archive pointers
- [docs/archive/](./docs/archive/) -- Snapshots of superseded markdown (`*.pre-audit-2026-04-21.md`) for easy diffing
