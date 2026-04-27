# Backend (FastAPI)

Python **FastAPI** service for the Litigation Prep Assistant: **Clerk JWT** auth (with **dev `X-User-Id` fallback**), **multipart** case intake, **SSE** streaming of the five-step agent pipeline, **SQLAlchemy async** persistence, **Pinecone** RAG, and **structlog** logging.

---

## Requirements

- Python **3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended)

---

## Install & run

```bash
cd backend
uv sync
uv run dev
```

Equivalent:

```bash
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000/docs` (Swagger) and `/redoc`
- Logging: configured at import in `src/main.py` (`configure_logging()`)

### Pinecone (RAG)

1. In the [Pinecone console](https://app.pinecone.io), create a **serverless** index: **1536** dimensions, **cosine** metric (required for `text-embedding-3-small`).
2. Copy **API key** and **index host** (URL under “Connect” / index details) into **`.env`** — see **`backend/.env.example`** (`PINECONE_API_KEY`, `PINECONE_INDEX_HOST` or `PINECONE_INDEX_NAME`, optional `PINECONE_NAMESPACE`).
3. Put statute text under repo **`data/raw/`** (`.txt` / `.md`), then from **`backend/`** run:

   `uv run python -m src.rag.ingestion`

   Without Pinecone configured, `rag_retrieve` returns no chunks (empty RAG) so the API still starts.

---

## Tests & lint (match CI)

```bash
uv run pytest tests/ -q          # 143 tests
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src --ignore-missing-imports
uv run pytest tests/ --cov=src --cov-fail-under=70 -q
```

Root `main.py` is a one-line **Uvicorn entry** (`uvicorn main:app`); Ruff allows the re-export via `# noqa: F401`.

---

## Golden-case evals & GitHub Actions

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). See **`docs/PROJECT_WALKTHROUGH.md`** §22 for tables and rubric mapping.

```bash
cd backend
uv run python -m evals.eval_extraction
uv run python -m evals.eval_llm_judge   # local only unless you dispatch the workflow
```

---

## Layout (`backend/src/`)

| Path | Role |
|------|------|
| `src/main.py` | FastAPI app, CORS, **HTTP request logging** middleware, global exception handler, routers |
| `src/core/config.py` | **pydantic-settings** (`DATABASE_URL`, `MODEL`, Pinecone, Clerk, CORS, timeouts, `APP_ENV`, `LOG_LEVEL`) |
| `src/core/logging.py` | **structlog** setup (JSON in production, console in dev) |
| `src/core/openai_client.py` | Shared OpenAI / OpenRouter client |
| `src/core/security.py` | Clerk **JWKS** JWT validation |
| `src/api/` | `routes_analyze`, `routes_cases`, `routes_auth`, `dependencies` |
| `src/agents/` | Orchestrator + extraction / strategy / drafting / QA + `prompts/` + `format_markdown.py` |
| `src/rag/` | `retriever.py`, `ingestion.py`, `pinecone_store.py`, `vector_store.py` (embedding + metadata constants) |
| `src/database/` | Async engine, `get_db`, models |
| `src/schemas/` | API + AI Pydantic models |
| `evals/` | **`golden_cases.json`** + **`eval_extraction`** / **`eval_llm_judge`** (see **Golden-case evals & GitHub Actions** above) |
| `tests/` | Pytest async suite (143 tests) |

Longer API and SSE details: **[`docs/backend.md`](../docs/backend.md)**. Full narrative: **[`docs/PROJECT_WALKTHROUGH.md`](../docs/PROJECT_WALKTHROUGH.md)**.

---

## API (summary)

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/health` | No auth |
| `GET` | `/api/v1/me` | Clerk **Bearer** token; in non-production, **`X-User-Id`** accepted if `Authorization` omitted |
| `POST` | `/api/v1/analyze` | **Multipart:** `title` (required), `case_text` (optional), `case_file` (optional `.txt`/`.md`/`.pdf`); at least one of typed text or file must yield non-empty merged text. **SSE** response |
| `GET` | `/api/v1/cases` | List cases (optional `?q=` title filter) |
| `GET` | `/api/v1/cases/{id}` | Case + steps |
| `DELETE` | `/api/v1/cases/{id}` | Delete case and steps |

---

## Environment

Copy **`backend/.env.example`** → **`.env`**. Key variables are documented there (`OPENAI_API_KEY` or `OPENROUTER_API_KEY`, `MODEL`, `DATABASE_URL`, `CLERK_JWKS_URL`, `ALLOWED_ORIGINS`, etc.).
