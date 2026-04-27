# Litigation Prep Assistant — Complete Project Walkthrough

> **Who this is for:** A beginner who wants to understand every part of this project in depth — what each file does, why it was built that way, how data flows from a user typing a case description to a finished legal brief appearing on screen, and what design decisions were made and why.

**Doc maintenance (2026-04-22):** Test counts match `uv run pytest tests/ -q` (**143** passed) and `pytest tests/ --collect-only -q`. Per‑file totals: `test_health` 3, `test_me` 5, `test_schemas` 26, `test_rag` 38, `test_analyze` 45, `test_history` 26. Audit trail: [`docs/DOCUMENTATION_AUDIT_LOG.md`](./DOCUMENTATION_AUDIT_LOG.md).

---

## Table of Contents

1. [What Does This Project Do?](#1-what-does-this-project-do)
2. [The Big Picture — Architecture Overview](#2-the-big-picture--architecture-overview)
3. [Repository Layout](#3-repository-layout)
4. [The Backend — FastAPI Application](#4-the-backend--fastapi-application)
   - 4.1 [Entry Point: `main.py`](#41-entry-point-mainpy)
   - 4.2 [Configuration: `core/config.py`](#42-configuration-coreconfigpy)
   - 4.3 [Logging: `core/logging.py`](#43-logging-coreloggingpy)
   - 4.4 [OpenAI Client: `core/openai_client.py`](#44-openai-client-coreopenai_clientpy)
   - 4.5 [Security: `core/security.py`](#45-security-coresecuritypy)
5. [The Database Layer](#5-the-database-layer)
   - 5.1 [ORM Models: `database/models.py`](#51-orm-models-databasemodelspy)
   - 5.2 [Sessions: `database/session.py`](#52-sessions-databasesessionpy)
6. [The API Routes](#6-the-api-routes)
   - 6.1 [Authentication Dependency: `api/dependencies.py`](#61-authentication-dependency-apidependenciespy)
   - 6.2 [Analyze Route: `api/routes_analyze.py`](#62-analyze-route-apiroutes_analyzepy)
   - 6.3 [Cases Route: `api/routes_cases.py`](#63-cases-route-apiroutes_casespy)
   - 6.4 [Auth Route: `api/routes_auth.py`](#64-auth-route-apiroutes_authpy)
7. [Data Schemas — The Contracts](#7-data-schemas--the-contracts)
   - 7.1 [AI Schemas: `schemas/ai_schemas.py`](#71-ai-schemas-schemasai_schemaspy)
   - 7.2 [API Schemas: `schemas/api_schemas.py`](#72-api-schemas-schemasapi_schemaspy)
8. [The AI Pipeline — Heart of the Project](#8-the-ai-pipeline--heart-of-the-project)
   - 8.1 [The Orchestrator: `agents/orchestrator.py`](#81-the-orchestrator-agentsorchestatorpy)
   - 8.2 [Agent 1 — Extraction: `agents/extraction.py`](#82-agent-1--extraction-agentsextractionpy)
   - 8.3 [Agent 2 — RAG Retrieval](#83-agent-2--rag-retrieval)
   - 8.4 [Agent 3 — Strategy: `agents/strategy.py`](#84-agent-3--strategy-agentsstrategypy)
   - 8.5 [Agent 4 — Drafting: `agents/drafting.py`](#85-agent-4--drafting-agentsdraftingpy)
   - 8.6 [Agent 5 — QA: `agents/qa.py`](#86-agent-5--qa-agentsqapy)
   - 8.7 [Markdown Formatter: `agents/format_markdown.py`](#87-markdown-formatter-agentsformat_markdownpy)
9. [The Prompts — Telling the Model What to Do](#9-the-prompts--telling-the-model-what-to-do)
   - 9.1 [Extraction Prompt](#91-extraction-prompt)
   - 9.2 [Strategy Prompt](#92-strategy-prompt)
   - 9.3 [Drafting Prompt](#93-drafting-prompt)
   - 9.4 [QA Prompt](#94-qa-prompt)
10. [The RAG System — Legal Knowledge Retrieval](#10-the-rag-system--legal-knowledge-retrieval)
    - 10.1 [Vector Store: `rag/vector_store.py`](#101-vector-store-ragvector_storepy)
    - 10.2 [Ingestion: `rag/ingestion.py`](#102-ingestion-ragingestionpy)
    - 10.3 [Retriever: `rag/retriever.py`](#103-retriever-ragretrieverpy)
11. [Services — Supporting Utilities](#11-services--supporting-utilities)
12. [Serializers — Database Query Helpers](#12-serializers--database-query-helpers)
13. [The Frontend — Next.js Application](#13-the-frontend--nextjs-application)
    - 13.1 [App Layout and Entry Points](#131-app-layout-and-entry-points)
    - 13.2 [New Scan Page — The Main Feature](#132-new-scan-page--the-main-feature)
    - 13.3 [Scans History Page](#133-scans-history-page)
    - 13.4 [API Client Library: `lib/api.ts`](#134-api-client-library-libapits)
    - 13.5 [Components](#135-components)
14. [Infrastructure — Docker and Deployment](#14-infrastructure--docker-and-deployment)
15. [Tests — How the Code is Verified](#15-tests--how-the-code-is-verified)
16. [Complete End-to-End Data Flow](#16-complete-end-to-end-data-flow)
17. [Key Design Decisions and Why They Were Made](#17-key-design-decisions-and-why-they-were-made)
18. [Rubric Self-Assessment](#18-rubric-self-assessment)
19. [Demo Script — What to Show and Say](#19-demo-script--what-to-show-and-say)
20. [How to Run the Code](#20-how-to-run-the-code)
21. [How to Run the Tests](#21-how-to-run-the-tests)
22. [Evals, Monitoring, and Logging — The Full Picture](#22-evals-monitoring-and-logging--the-full-picture)
23. [Improvements and Further Steps](#23-improvements-and-further-steps)

---

## 1. What Does This Project Do?

Imagine a Kenyan lawyer who receives a new case. They have pages of raw information: who the parties are, what happened, when it happened, and what the client wants. Turning that raw text into a polished legal brief that can be filed in court normally takes several hours of skilled work.

This project automates that process. A lawyer (or paralegal) types their case notes into a web form, clicks a button, and watches a structured legal brief assemble itself in real time — complete with extracted facts, legal strategies grounded in Kenyan statutes, a formally drafted court document, and a quality audit that checks for hallucinations or logical gaps.

The key technical achievement is that this is not a single "ask the AI" call. It is a **multi-agent pipeline**: five specialised AI agents, each doing one job extremely well, running in sequence and handing their output to the next agent.

---

## 2. The Big Picture — Architecture Overview

**Original figure (ASCII):**

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                            │
│  Next.js 16 (App Router)  ·  Clerk Auth  ·  React 19            │
│                                                                  │
│  /dashboard/new-scan  →  form → SSE stream → live Markdown UI   │
│  /dashboard/scans     →  case history list and detail view       │
└─────────────────────────────┬────────────────────────────────────┘
                              │  HTTPS / multipart form + SSE
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  Python 3.11  ·  Uvicorn ASGI  ·  Pydantic v2                   │
│                                                                  │
│  POST /api/v1/analyze  → runs pipeline, streams SSE              │
│  GET  /api/v1/cases    → returns case history                    │
│  GET  /api/v1/me       → returns current user                    │
└──────┬──────────────────────┬───────────────────────────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐    ┌──────────────────────────────────────────────┐
│ PostgreSQL  │    │            AI PIPELINE (5 agents)            │
│ (or SQLite) │    │                                              │
│             │    │  1. Extraction  (gpt-4o-mini + instructor)   │
│  • users    │    │  2. RAG         (ChromaDB + embeddings)      │
│  • cases    │    │  3. Strategy    (gpt-4o + instructor)        │
│  • steps    │    │  4. Drafting    (gpt-4o, plain text)         │
└─────────────┘    │  5. QA          (gpt-4o-mini + instructor)   │
                   └──────────────────┬───────────────────────────┘
                                      │
                              ┌───────▼────────┐
                              │  OpenAI API    │
                              │  (or          │
                              │  OpenRouter)   │
                              └────────────────┘
```

The same architecture is shown below as a **Mermaid** diagram: easier to read in GitHub, VS Code, and most Markdown preview tools that support Mermaid.

```mermaid
flowchart TB
    subgraph Browser["User's browser"]
        direction TB
        B_meta["Next.js 16 App Router · Clerk auth · React 19"]
        B_routes["/dashboard/new-scan — form, SSE, live Markdown UI<br/>/dashboard/scans — history and case detail"]
    end

    subgraph API["FastAPI backend"]
        direction TB
        F_meta["Python 3.11 · Uvicorn ASGI · Pydantic v2"]
        F_analyze["POST /api/v1/analyze — run pipeline, stream SSE"]
        F_cases["GET /api/v1/cases — case history"]
        F_me["GET /api/v1/me — current user"]
    end

    subgraph DB["Data store"]
        D_store[("PostgreSQL or SQLite<br/>users · cases · agent_steps")]
    end

    subgraph Agents["AI pipeline — five agents in order"]
        direction TB
        A1["1 · Extraction — gpt-4o-mini + instructor"]
        A2["2 · RAG — ChromaDB + embeddings"]
        A3["3 · Strategy — gpt-4o + instructor"]
        A4["4 · Drafting — gpt-4o, plain text"]
        A5["5 · QA — gpt-4o-mini + instructor"]
        A1 --> A2 --> A3 --> A4 --> A5
    end

    subgraph Models["Model providers"]
        OAI["OpenAI API · OpenRouter"]
    end

    Browser -->|HTTPS, multipart, SSE| API
    API --> DB
    API --> Agents
    Agents --> Models

    classDef browserStyle fill:#1e3a5f,stroke:#3b82f6,color:#fff
    classDef apiStyle fill:#3d2b5c,stroke:#8b5cf6,color:#fff
    classDef dbStyle fill:#0f3d2e,stroke:#10b981,color:#fff
    classDef agentStyle fill:#3d2f0f,stroke:#f59e0b,color:#fff
    classDef modelStyle fill:#0c2d3d,stroke:#06b6d4,color:#fff

    class B_meta,B_routes browserStyle
    class F_meta,F_analyze,F_cases,F_me apiStyle
    class D_store dbStyle
    class A1,A2,A3,A4,A5 agentStyle
    class OAI modelStyle
```

**The three layers are:**

1. **Frontend (Next.js)** — The user interface running in the browser. Built with React 19 and Next.js App Router. Uses Clerk for login. Streams results from the backend in real time using Server-Sent Events (SSE).

2. **Backend (FastAPI)** — A Python web server. Receives the case text, authenticates the user, runs the five-agent AI pipeline, saves everything to a database, and streams results back to the browser as they are produced.

3. **AI Pipeline** — Five agents that each call the OpenAI API with carefully crafted prompts. They run one after another, each feeding its output to the next. A RAG (Retrieval-Augmented Generation) step pulls in relevant Kenyan law from a local vector database.

---

## 3. Repository Layout

```
agent-juris/
│
├── README.md                   ← High-level project overview
├── Rubric.md                   ← Self-assessment against capstone rubric
│
├── backend/                    ← All Python code
│   ├── pyproject.toml          ← Python dependencies and tool config
│   ├── .env.example            ← Template for environment variables
│   └── src/
│       ├── main.py             ← FastAPI app factory (starting point)
│       ├── core/
│       │   ├── config.py       ← Environment variable settings
│       │   ├── logging.py      ← Structured logging setup
│       │   ├── openai_client.py← Single shared OpenAI client
│       │   └── security.py     ← Clerk JWT validation
│       ├── database/
│       │   ├── models.py       ← ORM table definitions
│       │   └── session.py      ← DB connection management
│       ├── schemas/
│       │   ├── ai_schemas.py   ← Pydantic models for AI outputs
│       │   └── api_schemas.py  ← Pydantic models for API inputs/outputs
│       ├── api/
│       │   ├── dependencies.py ← Auth dependency (who is calling?)
│       │   ├── routes_analyze.py← POST /analyze endpoint
│       │   ├── routes_auth.py  ← GET /me endpoint
│       │   └── routes_cases.py ← CRUD for case history
│       ├── agents/
│       │   ├── orchestrator.py ← Runs all 5 agents in sequence
│       │   ├── extraction.py   ← Agent 1: extract facts/entities/timeline
│       │   ├── strategy.py     ← Agent 3: legal strategy
│       │   ├── drafting.py     ← Agent 4: write the brief
│       │   ├── qa.py           ← Agent 5: quality audit
│       │   ├── format_markdown.py← Convert structured output to Markdown
│       │   └── prompts/        ← The actual text given to each model
│       │       ├── extraction.py
│       │       ├── strategy.py
│       │       ├── drafting.py
│       │       └── qa.py
│       ├── rag/
│       │   ├── vector_store.py ← ChromaDB client
│       │   ├── ingestion.py    ← Script to load legal docs into ChromaDB
│       │   └── retriever.py    ← Look up relevant Kenyan law
│       ├── services/
│       │   └── case_file_text.py← Parse uploaded PDF/TXT/MD files
│       └── serializers/
│           └── cases.py        ← DB queries for case history
│   └── tests/
│       ├── conftest.py         ← Shared fixtures, SSE helpers, DB overrides
│       ├── test_analyze.py     ← POST /analyze (45 tests)
│       ├── test_history.py     ← GET/DELETE /cases (26 tests)
│       ├── test_rag.py         ← Chunking, retriever, ingestion (38 tests)
│       ├── test_schemas.py     ← Pydantic AI/API schemas (26 tests)
│       ├── test_health.py      ← 3 tests
│       └── test_me.py          ← GET /me (5 tests)
│
├── frontend/                   ← All TypeScript/React code
│   ├── package.json            ← Node.js dependencies
│   ├── next.config.ts          ← Next.js configuration
│   └── src/
│       ├── app/                ← Next.js App Router pages
│       │   ├── layout.tsx      ← Root layout (Clerk + fonts)
│       │   ├── page.tsx        ← Landing page (/)
│       │   ├── dashboard/
│       │   │   ├── page.tsx    ← Dashboard home
│       │   │   ├── new-scan/
│       │   │   │   └── page.tsx← Case input + live streaming UI
│       │   │   └── scans/
│       │   │       ├── page.tsx← Case history list
│       │   │       └── [id]/
│       │   │           └── page.tsx← Individual case detail
│       ├── components/
│       │   ├── authenticated-layout.tsx← Sidebar/layout for logged-in users
│       │   └── pipeline-markdown-panel.tsx← Renders streamed Markdown output
│       ├── lib/
│       │   └── api.ts          ← All backend API calls
│       └── types/
│           └── case.ts         ← TypeScript type definitions
│
├── data/
│   ├── raw/                    ← Kenyan legal documents (txt/md files)
│   └── vector_db/              ← ChromaDB database files
│
└── infra/
    ├── Dockerfile.backend      ← Docker image for the backend
    └── docker-compose.yml      ← Runs PostgreSQL locally for development
```

---

## 4. The Backend — FastAPI Application

### What is FastAPI?
FastAPI is a modern Python web framework for building APIs. It is built on top of Python's `async`/`await` system, which means it can handle many requests at the same time without blocking. It also uses **Pydantic** to automatically validate the shape of data coming in and going out — if a request is missing a required field, FastAPI will automatically reject it with a clear error message before your code even runs.

### 4.1 Entry Point: `main.py`

**File:** [backend/src/main.py](../backend/src/main.py)

This is the very first file that runs when you start the server. Think of it as the "front door" of the application — it sets everything up and tells FastAPI where to find all the different routes.

```python
# Simplified conceptual view of what main.py does:

app = FastAPI(lifespan=lifespan)        # 1. Create the FastAPI app

app.add_middleware(CORSMiddleware)       # 2. Allow the browser to talk to this server
app.add_middleware(RequestLogger)        # 3. Log every incoming request

@app.exception_handler(Exception)       # 4. Catch any unhandled crash → return JSON error
async def global_exception_handler(request, exc): ...

app.include_router(analyze_router)       # 5. Register the /analyze endpoint
app.include_router(cases_router)         # 6. Register the /cases endpoints
app.include_router(auth_router)          # 7. Register the /me endpoint

@app.get("/health")                      # 8. Simple health check
async def health(): return {"status": "ok"}
```

**Key concept — Lifespan:** FastAPI supports a `lifespan` function that runs code when the server starts and when it stops. This is where the database tables are created (`init_db()`).

**Key concept — CORS Middleware:** Browsers have a security rule that prevents JavaScript on `localhost:3000` from talking to a server on `localhost:8000` unless the server explicitly allows it. The `CORSMiddleware` says "yes, I allow requests from the frontend origin."

**Key concept — Request Logger Middleware:** This wraps every single request. Before the request is processed, it notes the start time. After the response is sent, it logs the method (GET/POST), path (/api/v1/analyze), HTTP status code, and how many milliseconds it took. This is invaluable for debugging.

**Design decision — why a global exception handler?** Without it, if a bug causes an unhandled Python exception, FastAPI would return a generic 500 error with no useful information. The handler catches the exception, logs the full stack trace (so you can debug it), and returns a clean JSON response to the caller.

---

### 4.2 Configuration: `core/config.py`

**File:** [backend/src/core/config.py](../backend/src/core/config.py)

```python
class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./litigation.db"
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    model: str = "gpt-4o"
    clerk_jwks_url: str = ""
    allowed_origins: list[str] = ["http://localhost:3000"]
    agent_step_timeout_seconds: int = 120

settings = Settings()
```

Pydantic's `BaseSettings` reads values from environment variables (or a `.env` file). The field name `openai_api_key` maps to the environment variable `OPENAI_API_KEY` automatically.

**Why do this instead of just reading `os.environ["OPENAI_API_KEY"]` everywhere?**
- All configuration is in one place — easy to see what the app needs
- Pydantic validates types (e.g., `allowed_origins: list[str]` will parse `["http://localhost:3000"]` from a JSON string)
- Default values mean the app works locally without any `.env` file at all
- The single `settings` object is imported everywhere — no duplication

**Design decision — singleton pattern:** `settings = Settings()` runs once when the module is imported. Python caches module imports, so every file that does `from src.core.config import settings` gets the exact same object. No repeated environment variable parsing.

---

### 4.3 Logging: `core/logging.py`

**File:** [backend/src/core/logging.py](../backend/src/core/logging.py)

Logging is how you understand what your application is doing in production. `print()` statements work locally but are terrible in production — they have no timestamp, no severity level, and are hard to search through.

This project uses **structlog**, which produces structured JSON logs like:

```json
{
  "event": "llm_call_complete",
  "model": "gpt-4o-mini",
  "duration_ms": 1234,
  "prompt_tokens": 450,
  "completion_tokens": 320,
  "timestamp": "2026-04-22T10:30:00Z",
  "level": "info"
}
```

In development, structlog pretty-prints these as coloured console output. In production (`app_env == "production"`), it outputs newline-delimited JSON — one JSON object per line — which log aggregation services like Datadog or Papertrail can index and search.

**Key concept — log levels:**
- `DEBUG`: Extremely detailed, only useful during development
- `INFO`: Normal operations (request received, agent started)
- `WARNING`: Something unexpected but not broken (RAG returned no results)
- `ERROR`: Something failed (LLM call error, DB write failed)

**Design decision — why structlog over Python's built-in `logging`?** Python's standard `logging` module outputs plain text strings. Structlog adds key-value pairs to every log line, making logs *machine-readable*. You can then query "show me all requests where `duration_ms > 5000`" in a log tool.

---

### 4.4 OpenAI Client: `core/openai_client.py`

**File:** [backend/src/core/openai_client.py](../backend/src/core/openai_client.py)

```python
_client: AsyncOpenAI | None = None  # module-level singleton

def get_async_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = _build_client()
    return _client

def _build_client() -> AsyncOpenAI:
    if settings.openai_api_key:
        return AsyncOpenAI(api_key=settings.openai_api_key)
    elif settings.openrouter_api_key:
        return AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise RuntimeError("No API key configured")
```

All four AI agents call `get_async_client()`. This returns the same object every time.

**Why a singleton?** The `AsyncOpenAI` client maintains an HTTP connection pool internally. Creating a new client for each request would create and destroy connection pools constantly, which is slow and wasteful. A singleton means one pool shared by everyone.

**Why support OpenRouter?** OpenRouter is a proxy that gives you access to many different AI models (GPT-4o, Claude, Mistral, Llama) through one API key. This makes the project portable — you can switch between providers by changing one environment variable. The `base_url` parameter tells the OpenAI Python SDK to send requests to OpenRouter's API instead of OpenAI's.

---

### 4.5 Security: `core/security.py`

**File:** [backend/src/core/security.py](../backend/src/core/security.py)

This module validates that the user's identity token (JWT) is legitimate.

**What is a JWT (JSON Web Token)?** When a user logs in with Clerk (the authentication provider), Clerk gives their browser a signed token. This token is a string that contains the user's ID. When the browser calls the backend API, it sends this token in the `Authorization: Bearer <token>` header. The backend needs to verify: "Is this token really from Clerk, and has it not expired?"

**What is JWKS?** Clerk uses RSA cryptography to sign tokens. They publish their public keys at a well-known URL (the JWKS endpoint). The backend downloads these keys and uses them to verify the signature.

```python
# Simplified flow:
async def validate_clerk_jwt(token: str) -> dict:
    header = jwt.get_unverified_header(token)   # 1. Peek at header to get key ID
    kid = header["kid"]                          #    "Which key was used to sign this?"

    jwks = await _get_jwks(url)                  # 2. Download Clerk's public keys
    key = find_key_by_kid(jwks, kid)             # 3. Find the matching key

    payload = jwt.decode(token, key, ...)        # 4. Verify signature + expiry
    return payload                               # 5. Return {"sub": "user_123", ...}
```

**Key concept — JWKS caching:** Downloading the public keys on every single request would add ~200ms of network latency to every API call. The code caches the keys for 5 minutes (`_CACHE_TTL_SECONDS = 300`). If a key is not found in the cache (maybe Clerk rotated their keys), it forces a fresh download.

**Design decision — why not use a ready-made Clerk Python SDK?** The Clerk Python SDK exists but it is heavier and less flexible. Implementing JWT validation with PyJWT and httpx is about 70 lines of code and gives you complete control. The logic is straightforward and easier to test and debug.

---

## 5. The Database Layer

### 5.1 ORM Models: `database/models.py`

**File:** [backend/src/database/models.py](../backend/src/database/models.py)

**What is an ORM?** Instead of writing raw SQL like `SELECT * FROM cases WHERE user_id = '123'`, an ORM (Object-Relational Mapper) lets you work with Python objects. You define your table structure as Python classes, and SQLAlchemy generates the SQL.

The project has three tables:

**`users` table:**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True, nullable=False)  # from Clerk JWT
    email = Column(String, nullable=True)
    tier = Column(String, default="FREE")                   # FREE / PRO / ENTERPRISE
    created_at = Column(DateTime, default=datetime.utcnow)
```

**`cases` table:**
```python
class Case(Base):
    __tablename__ = "cases"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    raw_input = Column(Text, nullable=False)     # the original case text
    status = Column(String, default="PROCESSING") # PROCESSING / COMPLETED / FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    steps = relationship("AgentStep", back_populates="case")
```

**`agent_steps` table:**
```python
class AgentStep(Base):
    __tablename__ = "agent_steps"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID, ForeignKey("cases.id"), nullable=False)
    step_name = Column(String, nullable=False)   # "extraction", "strategy", etc.
    step_index = Column(Integer, nullable=False) # 0, 1, 2, 3, 4
    status = Column(String, default="PROCESSING")
    result = Column(JSON, nullable=True)         # the structured output
```

**Why three tables?** A `Case` is "parent" data — who submitted it, what the raw text was, what the overall status is. Each `AgentStep` is a child record representing one agent's work within that case. This separation means you can see exactly which agent succeeded and which failed, and retrieve the detailed output of any individual step for the history view.

**Why UUID primary keys instead of integers?** Integers are sequential and predictable — if you know case ID 42 exists, you might guess case ID 43 also exists. UUIDs are random 128-bit values, making it much harder to enumerate other users' data.

---

### 5.2 Sessions: `database/session.py`

**File:** [backend/src/database/session.py](../backend/src/database/session.py)

```python
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**What is `async`?** Python's `async` keyword marks a function that can be paused while waiting for I/O (like a database query or an API call). While it is paused, another request can use the same thread. This is why FastAPI can handle many concurrent requests without needing one thread per request.

**Why `expire_on_commit=False`?** By default, SQLAlchemy expires (invalidates) all loaded objects after a commit. This means accessing an attribute would trigger another database query. Setting this to `False` means objects stay loaded after commit, which is important when you need to access attributes after saving (like reading back the auto-generated `id`).

**`get_db()` as a FastAPI dependency:** This is a generator function that yields a database session. FastAPI's dependency injection system calls this, gives the session to your route function, and after the route function finishes, continues executing the rest of `get_db()` — which closes the session. This ensures sessions are never leaked.

---

## 6. The API Routes

### 6.1 Authentication Dependency: `api/dependencies.py`

**File:** [backend/src/api/dependencies.py](../backend/src/api/dependencies.py)

```python
async def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(alias="X-User-Id", default=None),
) -> CurrentUser:

    # Development shortcut: accept X-User-Id header
    if settings.app_env != "production" and x_user_id:
        return CurrentUser(user_id=x_user_id)

    # Production: validate the Clerk JWT
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authentication")

    token = authorization.removeprefix("Bearer ")
    payload = await validate_clerk_jwt(token, settings.clerk_jwks_url)
    user_id = payload.get("sub")
    return CurrentUser(user_id=user_id)
```

**What is a FastAPI dependency?** When you declare `current_user: CurrentUser = Depends(get_current_user)` in a route function, FastAPI automatically calls `get_current_user()` before your route runs, and injects the result as the `current_user` parameter. If `get_current_user` raises an `HTTPException`, the route never runs.

**Why a development shortcut?** In development, you do not want to set up a full Clerk account just to test the API. The `X-User-Id` header lets you pretend to be any user by just passing `X-User-Id: test-user-1` in a curl command or test. This shortcut is disabled in production (`app_env != "production"`).

---

### 6.2 Analyze Route: `api/routes_analyze.py`

**File:** [backend/src/api/routes_analyze.py](../backend/src/api/routes_analyze.py)

This is the main route — the one that actually runs the AI pipeline.

```python
@router.post("/analyze")
async def analyze(
    title: str = Form(...),
    case_text: str = Form(default=""),
    case_file: UploadFile | None = File(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:

    # 1. Validate and normalise title
    title = title.strip()
    if not title:
        raise HTTPException(422, "Title is required")

    # 2. If a file was uploaded, extract its text
    file_text = ""
    if case_file:
        file_text = await extract_uploaded_file_text(case_file)

    # 3. Merge form text + file text
    merged_text = merge_case_text_and_file(case_text, file_text)
    if not merged_text.strip():
        raise HTTPException(422, "Case text is required")

    # 4. Run the pipeline as a streaming response
    request_model = AnalyzePipelineInput(title=title, raw_case_text=merged_text)
    return StreamingResponse(
        run_pipeline(request_model, current_user.user_id, db),
        media_type="text/event-stream"
    )
```

**What is `Form(...)`?** The form data is sent as `multipart/form-data` (the same format browsers use for HTML forms with file uploads). `Form(...)` tells FastAPI to read the field from the form body. The `...` means it is required.

**What is `StreamingResponse`?** Normally an API endpoint collects all its data, then sends one big response. `StreamingResponse` is different — it sends data as it becomes available. The route wraps the `run_pipeline()` async generator, which yields pieces of the response (SSE events) as each agent finishes. The browser receives these incrementally and updates the UI in real time.

**What is SSE (Server-Sent Events)?** SSE is a simple protocol where the server sends events over a long-lived HTTP connection. Each event looks like:
```
data: {"type": "markdown_section", "section_id": "extraction", ...}\n\n
```
The browser **`fetch`** API reads the response body as a **`ReadableStream`** (see `frontend/src/lib/api.ts`) and splits SSE `data:` lines manually — **`EventSource`** is not used for `POST /analyze` because it cannot send multipart bodies or custom headers.

---

### 6.3 Cases Route: `api/routes_cases.py`

**File:** [backend/src/api/routes_cases.py](../backend/src/api/routes_cases.py)

Three endpoints for managing case history:

- `GET /cases` — List all cases for the current user (with optional title search)
- `GET /cases/{analysis_id}` — Get all details for one case (including all agent step outputs)
- `DELETE /cases/{analysis_id}` — Delete a case and all its steps

All three are protected by `Depends(get_current_user)` — you can only see and delete your own cases. The ownership check is done in the serializer: the SQL query always filters by both `case_id` AND `user_id`, so even if you guess another user's case UUID, the query returns nothing.

---

### 6.4 Auth Route: `api/routes_auth.py`

**File:** [backend/src/api/routes_auth.py](../backend/src/api/routes_auth.py)

A minimal route that just returns the current user's ID (and optional email). Used by the frontend to confirm the user is authenticated and get their identity.

---

## 7. Data Schemas — The Contracts

### 7.1 AI Schemas: `schemas/ai_schemas.py`

**File:** [backend/src/schemas/ai_schemas.py](../backend/src/schemas/ai_schemas.py)

These Pydantic models define the exact structure that each AI agent must return. Think of them as contracts: "I promise to give you an `ExtractionResult` object that has `core_facts`, `entities`, and `chronological_timeline`."

```python
class Entity(BaseModel):
    name: str               # e.g. "Wanjiru Holdings Ltd"
    type: str               # e.g. "company"
    role: str               # e.g. "plaintiff"

class TimelineEvent(BaseModel):
    date: str               # e.g. "2023-03-15"
    event: str              # e.g. "Contract signed for supply of goods"

class ExtractionResult(BaseModel):
    core_facts: list[str]
    entities: list[Entity]
    chronological_timeline: list[TimelineEvent]
```

**Why Pydantic models instead of raw dictionaries?** With a dictionary, you would do `result["core_facts"]` and get a `KeyError` if the model hallucinated a different field name. With Pydantic, the structure is validated on creation — if the model returns `{"key_facts": [...]}` instead of `{"core_facts": [...]}`, Pydantic raises a `ValidationError` immediately, which `instructor` then uses to retry the model call.

---

### 7.2 API Schemas: `schemas/api_schemas.py`

**File:** [backend/src/schemas/api_schemas.py](../backend/src/schemas/api_schemas.py)

These define what the API sends to and receives from the frontend.

```python
class AnalyzePipelineInput(BaseModel):
    title: str
    raw_case_text: str

    @field_validator("title", "raw_case_text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()
```

The `@field_validator` decorator runs the validation function whenever a new `AnalyzePipelineInput` is created. If the title is empty or just spaces, Pydantic raises a `ValidationError` before any AI call is made.

---

## 8. The AI Pipeline — Heart of the Project

### 8.1 The Orchestrator: `agents/orchestrator.py`

**File:** [backend/src/agents/orchestrator.py](../backend/src/agents/orchestrator.py)

The orchestrator is the most important file in the entire project. It coordinates all five agents, manages the database, handles retries, and streams results to the browser.

```python
async def run_pipeline(
    request: AnalyzePipelineInput,
    user_id: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:          # yields SSE strings
```

It is an `AsyncGenerator` — a function that uses `yield` to send data back to the caller one piece at a time, without returning all at once.

**How SSE events are formatted:**

```python
def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"
```

Every event is a string starting with `data: `, containing JSON, and ending with two newlines. The two newlines are part of the SSE protocol — they signal the end of one event.

**The five pipeline steps in order:**

```
Step 0 — Extraction
   Input:  raw_case_text (what the user typed)
   Does:   Parse facts, entities, timeline from the raw text
   Output: ExtractionResult
   ↓
Step 1 — RAG Retrieval
   Input:  core_facts from extraction (joined as a query string)
   Does:   Search ChromaDB for relevant Kenyan legal precedents
   Output: list[str] (chunks of legal text)
   ↓
Step 2 — Strategy
   Input:  ExtractionResult + RAG chunks
   Does:   Identify legal issues, map to Kenyan statutes, form arguments
   Output: StrategyResult
   ↓
Step 3 — Drafting
   Input:  ExtractionResult + StrategyResult
   Does:   Write a formal Kenyan High Court brief in Markdown
   Output: DraftingResult
   ↓
Step 4 — QA
   Input:  ExtractionResult + DraftingResult.brief_markdown
   Does:   Audit for hallucinations, missing logic, inconsistencies
   Output: QAResult
```

**How the database is updated at each step:**

```python
async def _start_step(db, case_id, step_name, step_index) -> AgentStep:
    step = AgentStep(
        case_id=case_id, step_name=step_name,
        step_index=step_index, status="PROCESSING"
    )
    db.add(step)
    await db.commit()
    return step

async def _finish_step(db, step, result_dict) -> None:
    step.status = "COMPLETED"
    step.result = result_dict
    await db.commit()
```

Before each agent runs, a `PROCESSING` step record is written to the database. After the agent finishes, the record is updated to `COMPLETED` with the result. If the agent fails, it is marked `FAILED`.

**Retry logic:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

async def _run_with_retry(coro_fn, *args):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError))
    )
    async def _inner():
        return await coro_fn(*args)
    return await _inner()
```

**What is `tenacity`?** It is a Python library for retrying functions. This retry decorator says: "If the call raises `RateLimitError`, `APIConnectionError`, or `APITimeoutError`, wait 2-10 seconds (doubling each time) and try again, up to 3 times total."

**Why exponential backoff?** OpenAI's rate limits kick in when you make too many requests too quickly. If you immediately retry, you will likely hit the rate limit again. Waiting a bit (2s, then 4s, then 8s) gives the limit time to reset. The "doubling" strategy is called exponential backoff.

**Critical vs. non-critical steps:**

RAG retrieval (Step 1) and QA (Step 4) are wrapped in try/except blocks with `continue` — if they fail, the pipeline continues rather than crashing. The brief can still be generated without RAG context (it will just lack Kenyan law precedents), and the QA audit is informational rather than blocking.

**After all agents complete:**

```python
# Mark the case as COMPLETED
case.status = "COMPLETED"
await db.commit()

# Emit the final event with the case ID
yield _sse({"type": "complete", "case_id": str(case.id)})
```

The `complete` event gives the browser the `case_id` UUID so it can link to the detail view.

**On failure:**

```python
except Exception as exc:
    case.status = "FAILED"
    await db.commit()
    yield _sse({"type": "error", "detail": str(exc)})
```

---

### 8.2 Agent 1 — Extraction: `agents/extraction.py`

**File:** [backend/src/agents/extraction.py](../backend/src/agents/extraction.py)

The first agent reads the raw case notes and pulls out:
- **Core facts**: The key legally significant statements (at least 5)
- **Entities**: Named parties, places, documents, statutes involved
- **Timeline**: Chronological sequence of events with ISO 8601 dates

**What is `instructor`?**

```python
import instructor
from openai import AsyncOpenAI

client = instructor.from_openai(get_async_client(), mode=instructor.Mode.JSON)

result = await client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=ExtractionResult,   # ← the Pydantic schema
    messages=[...]
)
# result is guaranteed to be an ExtractionResult instance
```

`instructor` is a library that wraps the OpenAI client. It:
1. Takes your Pydantic model (`ExtractionResult`) and converts it to a JSON schema
2. Adds that schema to the prompt as instructions ("respond only with JSON matching this schema")
3. Calls the OpenAI API
4. Parses the JSON response back into a Pydantic object
5. If the response is malformed or missing fields, **automatically retries with an error message** like "Your response was missing the required field `core_facts`"

**Why `gpt-4o-mini` for extraction instead of `gpt-4o`?** Extraction is a relatively straightforward information extraction task — the model does not need to reason deeply, just identify and format information. `gpt-4o-mini` is about 10× cheaper and faster than `gpt-4o`. Saving costs here means more budget for the harder strategic reasoning task.

**The few-shot example:** The messages array includes a complete worked example: a Kenyan supply-of-goods dispute with its corresponding JSON output. The model sees this example before seeing the real case, which teaches it exactly what format and level of detail is expected. This technique — called **few-shot prompting** — dramatically improves output consistency.

---

### 8.3 Agent 2 — RAG Retrieval

RAG stands for **Retrieval-Augmented Generation**. Instead of relying solely on what the model was trained on (which may not include specific Kenyan statutes), the system maintains a database of Kenyan legal documents. Before the strategy agent runs, it retrieves the most relevant excerpts and provides them to the model as context.

The retrieval is done by the `rag_retrieve()` function (see Section 10). The orchestrator calls it with the extracted core facts as a query string, gets back a list of relevant text chunks, and passes them to the strategy agent.

---

### 8.4 Agent 3 — Strategy: `agents/strategy.py`

**File:** [backend/src/agents/strategy.py](../backend/src/agents/strategy.py)

The strategy agent receives the extraction output and the RAG context, and produces a complete legal strategy:

```python
class StrategyResult(BaseModel):
    legal_issues: list[str]            # Distinct legal questions raised
    applicable_laws: list[str]          # Kenyan statutes and sections
    arguments: list[LegalArgument]      # Each argument with issue, law, summary
    counterarguments: list[Counterargument]  # Opponent's likely responses
    legal_reasoning: str                # Overall analysis paragraph
```

**How the input is constructed:**

```python
def _build_user_content(extraction: ExtractionResult, rag_context: list[str]) -> str:
    return json.dumps({
        "core_facts": extraction.core_facts,
        "timeline": [e.model_dump() for e in extraction.chronological_timeline],
        "entities": [e.model_dump() for e in extraction.entities],
        "legal_context_from_precedents": rag_context,
    }, indent=2)
```

The model receives a well-structured JSON object with all the context it needs. This is better than a free-form paragraph because the model can clearly distinguish between "what the client told us" and "what relevant law says."

**This agent uses the configurable `settings.model`** (defaulting to `gpt-4o`) rather than hardcoding `gpt-4o-mini`. The legal strategy task requires sophisticated multi-step reasoning — identifying issues, finding applicable law, forming coherent arguments — which benefits from the larger, more capable model.

---

### 8.5 Agent 4 — Drafting: `agents/drafting.py`

**File:** [backend/src/agents/drafting.py](../backend/src/agents/drafting.py)

The drafting agent is the only one that does **not** use `instructor` / JSON mode. Its output is a full Markdown document, not structured data, so there is no Pydantic schema to validate against. The model is simply asked to write text.

```python
class DraftingResult(BaseModel):
    brief_markdown: str    # The entire brief as a Markdown string
```

The prompt instructs the model to write exactly this structure:

```markdown
# IN THE MATTER OF [case title]

## PARTIES
- Claimant: [name and description]
- Respondent: [name and description]

## FACTS
[numbered paragraphs in passive voice, third person]

## LEGAL ISSUES
[numbered list]

## LEGAL ARGUMENTS
### Issue 1: [issue]
[argument]

#### RESPONDENT'S ANTICIPATED POSITION
[counterargument and rebuttal]

## CONCLUSION AND PRAYER FOR RELIEF
[formal closing]
```

**Why does the drafting agent receive both extraction AND strategy?** The facts come from extraction (ensuring fidelity to the original case). The arguments and law come from strategy. The drafting agent's only job is to write fluent, formally-worded Kenyan court prose combining both inputs.

---

### 8.6 Agent 5 — QA: `agents/qa.py`

**File:** [backend/src/agents/qa.py](../backend/src/agents/qa.py)

The QA agent audits the finished brief. It reads the brief alongside the original facts and checks for:

1. **Hallucinations**: Did the brief mention facts not in the original case notes?
2. **Statute verification**: Are the cited Kenyan laws real and plausible? (e.g., citing "Section 99 of the Contract Act" when that section does not exist)
3. **Logical gaps**: Are there legal issues raised but not argued?
4. **Internal consistency**: Does the conclusion follow from the arguments?

```python
class QAResult(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    hallucination_warnings: list[str]
    missing_logic: list[str]
    risk_notes: list[str]
```

**Risk level criteria:**
- `HIGH` — There are hallucinations or fabricated citations (the brief would embarrass the lawyer if filed)
- `MEDIUM` — Logical gaps or unaddressed issues (needs human review before filing)
- `LOW` — Only stylistic issues (ready for final review)

**Why does this agent exist?** LLMs are known to confidently generate plausible-sounding but false information (hallucination). In a legal context, citing a non-existent statute could be professionally damaging. The QA agent cannot guarantee correctness — it is itself an LLM — but it adds a second layer of scrutiny with different prompting, which catches many common errors.

---

### 8.7 Markdown Formatter: `agents/format_markdown.py`

**File:** [backend/src/agents/format_markdown.py](../backend/src/agents/format_markdown.py)

Each agent produces structured Pydantic objects. Before streaming them to the browser, the orchestrator converts them to readable Markdown. This file provides one converter function per agent:

```python
def extraction_to_markdown(result: ExtractionResult) -> str:
    lines = ["## Core Facts"]
    for fact in result.core_facts:
        lines.append(f"- {fact}")
    lines.append("\n## Entities")
    for entity in result.entities:
        lines.append(f"- **{entity.name}** — {entity.type} — {entity.role}")
    # ... etc.
    return "\n".join(lines)
```

**Why convert to Markdown rather than sending the raw JSON?** The frontend renders Markdown using `react-markdown`. Markdown is human-readable in a way JSON is not. A bullet list of facts is much clearer than `{"core_facts": ["fact 1", "fact 2"]}` when displayed to a lawyer who is not a developer.

---

## 9. The Prompts — Telling the Model What to Do

### 9.1 Extraction Prompt

**File:** [backend/src/agents/prompts/extraction.py](../backend/src/agents/prompts/extraction.py)

The extraction prompt tells the model it is a "Kenyan paralegal with 10 years of experience." This technique — giving the model a persona — has been shown to improve domain-specific output quality because it activates the model's legal knowledge and sets appropriate expectations.

**Key rules embedded in the prompt:**
- Facts must be "legally significant" and "atomic" (one fact per bullet)
- Entity types are strictly enumerated: `person | company | government_body | place | document | court | contract | statute`
- Dates must be ISO 8601 format (`YYYY-MM-DD`), falling back to `YYYY-MM` or `unknown`

**The few-shot example is in the prompts file:**
```python
FEW_SHOT_USER = """
Wanjiru Holdings Ltd, a supplier of office furniture, entered into a contract
with Nairobi County Government on 15 January 2022 for the supply of furniture
worth KSh 4.5 million...
"""

FEW_SHOT_ASSISTANT = """
{
  "core_facts": [
    "Wanjiru Holdings Ltd entered into a supply contract with Nairobi County Government on 15 January 2022",
    ...
  ],
  ...
}
"""
```

The few-shot example is carefully crafted around a realistic Kenyan commercial dispute, so the format is familiar to what real cases look like.

**Prompt version tracking:** `PROMPT_VERSION = "v1.1"` is logged with every extraction call. This allows you to correlate model output quality with prompt changes over time.

---

### 9.2 Strategy Prompt

**File:** [backend/src/agents/prompts/strategy.py](../backend/src/agents/prompts/strategy.py)

The strategy prompt adopts the persona of a "senior Kenyan litigation attorney." Key constraints:
- "Only use Kenyan law" — prevents the model from citing English or American cases
- "Quote precedents from the RAG context" — grounds citations in retrieved documents
- "Do not fabricate citations" — directly addresses hallucination risk

---

### 9.3 Drafting Prompt

**File:** [backend/src/agents/prompts/drafting.py](../backend/src/agents/prompts/drafting.py)

The drafting prompt adopts the persona of a "senior advocate with 15 years of Kenyan High Court experience." It specifies:
- "Third person, passive voice, no contractions" — formal Kenyan court writing style
- "Cite specific statute sections with cap/act number" — prevents vague citations like "the law says..."
- The exact section structure the brief must follow

---

### 9.4 QA Prompt

**File:** [backend/src/agents/prompts/qa.py](../backend/src/agents/prompts/qa.py)

The QA prompt positions the model as a "senior legal QA reviewer at a Kenyan law firm." The prompt gives explicit criteria for each risk level, reducing ambiguity in the model's risk assessment.

---

## 10. The RAG System — Legal Knowledge Retrieval

### What is RAG?

RAG (Retrieval-Augmented Generation) solves a key problem: the OpenAI model's training data does not include every Kenyan statute and legal precedent. Even if it did, models sometimes misremember or confabulate legal details.

The solution is to maintain a local database of Kenyan legal documents. When the strategy agent needs context, relevant excerpts are retrieved and inserted directly into the prompt — not as training data, but as literal text the model reads in real time.

### 10.1 Vector Store: `rag/vector_store.py`

**File:** [backend/src/rag/vector_store.py](../backend/src/rag/vector_store.py)

ChromaDB is an open-source vector database. It stores documents as high-dimensional vectors (embeddings). Two documents with similar meaning will have similar vectors, even if they use different words.

```python
COLLECTION_NAME = "kenyan_legal_corpus"
EMBED_MODEL = "text-embedding-3-small"
DEFAULT_PERSIST_DIR = "data/vector_db/"

def get_collection(client: PersistentClient) -> Collection:
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # cosine similarity search
    )
```

**Cosine similarity** measures the angle between two vectors. A similarity of 1.0 means identical direction (very similar meaning); 0.0 means perpendicular (no semantic relationship). It is better than Euclidean distance for text embeddings because it handles documents of different lengths fairly.

---

### 10.2 Ingestion: `rag/ingestion.py`

**File:** [backend/src/rag/ingestion.py](../backend/src/rag/ingestion.py)

This script (run once before the server starts) reads Kenyan legal documents from `data/raw/` and loads them into ChromaDB.

```python
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap    # overlap ensures context is not lost at boundaries
    return chunks
```

**Why chunk text instead of embedding the whole document?**
1. OpenAI's embedding model has a token limit — very long documents cannot fit
2. Smaller chunks are more precise — when you retrieve "the 5 most relevant chunks," you get 5 focused excerpts rather than 5 entire documents
3. Cosine similarity works better on focused text than on documents covering many topics

**Why 100 characters of overlap?** A sentence split across a chunk boundary would lose context. The overlap ensures the end of one chunk and the beginning of the next both contain that sentence, so neither loses the context.

**The embedding process:**
```python
# One call embeds ALL chunks at once (batching is more efficient)
response = await client.embeddings.create(
    input=texts,           # list of 800-char strings
    model="text-embedding-3-small"
)
embeddings = [item.embedding for item in response.data]
```

Each 800-character text chunk becomes a 1536-dimension vector (list of 1536 floating point numbers). ChromaDB stores both the original text and its embedding.

---

### 10.3 Retriever: `rag/retriever.py`

**File:** [backend/src/rag/retriever.py](../backend/src/rag/retriever.py)

```python
async def rag_retrieve(query: str, top_k: int = 5) -> list[str]:
    if not query.strip():
        return []

    # 1. Embed the query using the same model used for ingestion
    response = await openai_client.embeddings.create(
        input=[query], model=EMBED_MODEL
    )
    query_vector = response.data[0].embedding

    # 2. Search ChromaDB for nearest neighbours
    results = await asyncio.to_thread(
        collection.query,
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    return results["documents"][0]  # list of matching text chunks
```

**Why `asyncio.to_thread()`?** ChromaDB's query method is synchronous (blocking). In an async Python application, blocking calls on the main thread would freeze all other concurrent requests. `asyncio.to_thread()` runs the blocking call in a separate thread pool, freeing the event loop to handle other requests while waiting.

**How the query is formed:** The orchestrator uses the core facts as the query string: `" ".join(extraction_result.core_facts)`. This gives a natural-language query like "supply of goods contract breach Nairobi County Government KSh 4.5 million non-payment," which will have high cosine similarity to legal documents about contract breaches and government procurement.

---

## 11. Services — Supporting Utilities

### `services/case_file_text.py`

**File:** [backend/src/services/case_file_text.py](../backend/src/services/case_file_text.py)

Handles uploaded files. A lawyer may want to upload an existing case document rather than re-typing the facts.

```python
async def extract_uploaded_file_text(upload: UploadFile) -> str:
    content = await upload.read()
    suffix = Path(upload.filename).suffix.lower()

    if suffix in (".txt", ".md"):
        return content.decode("utf-8", errors="replace")

    elif suffix == ".pdf":
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    else:
        raise HTTPException(415, f"Unsupported file type: {suffix}")
```

**Why `errors="replace"` when decoding text files?** A user might upload a file with non-UTF-8 characters (e.g., a document saved in Windows-1252 encoding). Rather than crashing with a `UnicodeDecodeError`, `errors="replace"` substitutes a replacement character (`�`) for any undecodable bytes, preserving the rest of the text.

**Why `pypdf`?** PDF files are binary formats — you cannot read them like text. `pypdf` parses the PDF structure and extracts text content from each page. For complex PDFs with images or scanned text, this may not work perfectly, but it handles the common case of digitally created documents.

---

## 12. Serializers — Database Query Helpers

### `serializers/cases.py`

**File:** [backend/src/serializers/cases.py](../backend/src/serializers/cases.py)

Serializers isolate database queries from route logic. The routes call serializer functions; the serializers write SQL.

```python
async def fetch_cases_for_user(
    db: AsyncSession,
    user_id: str,
    title_query: str | None = None,
) -> list[Case]:
    query = (
        select(Case)
        .where(Case.user_id == user_id)
        .order_by(Case.created_at.desc())
    )
    if title_query:
        query = query.where(Case.title.ilike(f"%{title_query}%"))
    result = await db.execute(query)
    return list(result.scalars().all())
```

**Why `ilike`?** `ilike` is a case-insensitive LIKE pattern match. `Case.title.ilike(f"%{title_query}%")` matches any title containing the search term, regardless of case. PostgreSQL supports `ilike` natively; SQLAlchemy translates it appropriately.

**Why separate serializers from routes?** Routes should handle HTTP concerns (request parsing, response formatting, authentication). Database concerns belong in a separate layer. This makes it easy to add a second consumer of the same queries (e.g., a CLI tool, a background job) without duplicating the SQL.

---

## 13. The Frontend — Next.js Application

### What is Next.js App Router?

Next.js is a React framework. "App Router" is the modern routing system (introduced in Next.js 13) where each folder in `src/app/` corresponds to a URL path. A file named `page.tsx` in that folder defines what renders at that URL.

By default, components are **React Server Components** — they render on the server. You add `"use client"` at the top to make a component a **Client Component** — one that runs in the browser and can use React hooks like `useState` and `useEffect`.

---

### 13.1 App Layout and Entry Points

**File:** [frontend/src/app/layout.tsx](../frontend/src/app/layout.tsx)

The root layout wraps every page. It provides:
- `ClerkProvider` — makes Clerk authentication available to all components
- Google Geist fonts — typography
- `AuthenticatedLayout` — conditionally shows sidebar for logged-in users

**File:** [frontend/src/app/page.tsx](../frontend/src/app/page.tsx)

The landing page (`/`). Uses Clerk's `<SignedOut>` and `<SignedIn>` components to conditionally render:
- Signed-out users see a marketing landing page
- Signed-in users are automatically redirected to `/dashboard`

---

### 13.2 New Scan Page — The Main Feature

**File:** [frontend/src/app/dashboard/new-scan/page.tsx](../frontend/src/app/dashboard/new-scan/page.tsx)

This is the most important frontend page. A user fills in a form and watches the AI pipeline run in real time.

**State management:**

```typescript
const [title, setTitle] = useState("");
const [caseText, setCaseText] = useState("");
const [file, setFile] = useState<File | null>(null);
const [sections, setSections] = useState<MarkdownSection[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const abortRef = useRef<AbortController | null>(null);
```

- `sections` accumulates the Markdown output as each agent finishes. New sections are appended, never replacing existing ones.
- `abortRef` holds an `AbortController` — a browser API that lets you cancel an in-progress HTTP request. The "Stop" button calls `abortRef.current.abort()`.

**Form submission flow:**

```typescript
const handleSubmit = async () => {
    // 1. Validate inputs
    if (!title.trim()) { setError("Title is required"); return; }
    if (!caseText.trim() && !file) { setError("Provide case text or a file"); return; }

    // 2. Set up AbortController for cancellation
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setSections([]);

    // 3. Stream the SSE response
    await postAnalyzeStream(
        { title, caseText, file },
        userId,
        controller.signal,
        (payload) => {
            if (payload.type === "markdown_section") {
                setSections(prev => [...prev, payload]);   // append new section
            } else if (payload.type === "error") {
                setError(payload.detail);
            }
        },
        (err) => setError(err.message)
    );
    setLoading(false);
};
```

**Why `[...prev, payload]` instead of `setSections(sections.concat(payload))`?** React state updates are batched. Using the functional form `prev => [...prev, payload]` ensures you always append to the latest state, not a stale closure value — important when multiple SSE events arrive in rapid succession.

---

### 13.3 Scans History Page

**File:** [frontend/src/app/dashboard/scans/page.tsx](../frontend/src/app/dashboard/scans/page.tsx)

Shows the user's case history with search and delete functionality.

**Debounced search:**

```typescript
const [search, setSearch] = useState("");
const [debouncedSearch, setDebouncedSearch] = useState("");

useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
}, [search]);

useEffect(() => {
    fetchCases(debouncedSearch);
}, [debouncedSearch]);
```

**What is debouncing?** Without debouncing, every keypress in the search box would trigger an API call. For the word "contract," that is 8 API calls. Debouncing waits 300ms after the user stops typing before making the call. The `clearTimeout` in the cleanup function cancels any pending timer when the component re-renders, ensuring only the final value is sent.

**Delete with confirmation:**

```typescript
const handleDelete = async (caseId: string) => {
    if (!confirm("Delete this scan?")) return;
    setDeletingId(caseId);
    await deleteCase(caseId, userId);
    setItems(prev => prev.filter(item => item.id !== caseId));
    setDeletingId(null);
};
```

After deletion, the item is removed from local state immediately (`filter`), so the UI updates instantly without a refetch.

---

### 13.4 API Client Library: `lib/api.ts`

**File:** [frontend/src/lib/api.ts](../frontend/src/lib/api.ts)

All backend API calls are centralised here. Components import from this file — they never construct URLs or parse responses directly.

**SSE streaming:**

```typescript
export async function postAnalyzeStream(
    input: AnalyzeFormInput,
    userId: string,
    signal: AbortSignal,
    onSseData: (payload: SseAnalyzePayload) => void,
    onError: (err: Error) => void,
): Promise<void> {
    const formData = new FormData();
    formData.append("title", input.title);
    formData.append("case_text", input.caseText);
    if (input.file) formData.append("case_file", input.file);

    const response = await fetch(`${apiBaseUrl}/api/v1/analyze`, {
        method: "POST",
        headers: { "X-User-Id": userId },
        body: formData,
        signal,    // ← AbortController signal for cancellation
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse complete SSE events (terminated by \n\n)
        const events = buffer.split("\n\n");
        buffer = events.pop()!;   // last element may be incomplete

        for (const event of events) {
            if (event.startsWith("data: ")) {
                const json = event.slice(6);    // strip "data: "
                onSseData(JSON.parse(json));
            }
        }
    }
}
```

**Why manual SSE parsing instead of `EventSource`?** Same rationale as above: **`EventSource` is GET-only** and cannot send **`multipart/form-data`** or arbitrary headers. The repo uses a small **`fetch` + `ReadableStream`** parser (`postAnalyzeStream`). You could swap in `@microsoft/fetch-event-source` if you prefer its reconnect semantics — functionally equivalent for this API.

---

### 13.5 Components

**File:** [frontend/src/components/pipeline-markdown-panel.tsx](../frontend/src/components/pipeline-markdown-panel.tsx)

```typescript
export function PipelineMarkdownPanel({ sections, streaming }: Props) {
    if (sections.length === 0) {
        return <p>{streaming ? "Waiting for output…" : emptyMessage}</p>;
    }
    return (
        <>
            {sections.map((section) => (
                <details key={section.section_id}>
                    <summary>{section.heading}</summary>
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                        {section.markdown}
                    </ReactMarkdown>
                </details>
            ))}
        </>
    );
}
```

**Why `<details>` / `<summary>`?** HTML's native disclosure element creates collapsible sections with no JavaScript. The user can collapse sections they have already read to focus on later ones. As new sections arrive via SSE, they are appended in open state.

**Why `remark-gfm`?** GitHub Flavored Markdown adds support for tables, task lists, and strikethrough. The drafting agent produces Markdown with bold text and section headers, which `remark-gfm` renders correctly.

---

## 14. Infrastructure — Docker and Deployment

### `infra/Dockerfile.backend`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`PYTHONDONTWRITEBYTECODE=1`** — Prevents Python from writing `.pyc` files inside the container, keeping the image smaller.

**`PYTHONUNBUFFERED=1`** — Ensures print statements and log output appear immediately in Docker's log stream rather than being buffered. Critical for seeing live logs.

**`--host 0.0.0.0`** — By default, Uvicorn binds to `127.0.0.1` (localhost only). `0.0.0.0` makes it listen on all network interfaces, which is required inside a container.

### `infra/docker-compose.yml`

For local development, you can start a PostgreSQL 16 database with one command:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: litigation
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

The `postgres_data` volume persists your data between `docker compose down` / `docker compose up` cycles.

---

## 15. Tests — How the Code is Verified

### `tests/conftest.py`

**File:** [backend/tests/conftest.py](../backend/tests/conftest.py)

`conftest.py` is a special pytest file — fixtures defined here are available to all tests automatically.

**The most important fixture is `mock_agents`:**

```python
# conftest.py (imports): from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_agents():
    with (
        patch("src.agents.orchestrator.run_extraction_agent", new_callable=AsyncMock) as m_ext,
        patch("src.agents.orchestrator.run_strategy_agent", new_callable=AsyncMock) as m_strat,
        patch("src.agents.orchestrator.run_drafting_agent", new_callable=AsyncMock) as m_draft,
        patch("src.agents.orchestrator.run_qa_agent", new_callable=AsyncMock) as m_qa,
        patch("src.agents.orchestrator.rag_retrieve", new_callable=AsyncMock) as m_rag,
    ):
        m_ext.return_value = MOCK_EXTRACTION
        m_strat.return_value = MOCK_STRATEGY
        m_draft.return_value = MOCK_DRAFT
        m_qa.return_value = MOCK_QA
        m_rag.return_value = []  # default: empty RAG; tests may override
        yield {"extraction": m_ext, "strategy": m_strat, "drafting": m_draft, "qa": m_qa, "rag": m_rag}
```

Patches are applied **where the orchestrator binds the name** (`src.agents.orchestrator.*`), not inside each agent module. This replaces real LLM/RAG calls with mocks that return **`MOCK_*`** fixtures from `conftest.py`. Tests therefore:
1. Run in milliseconds (no API calls)
2. Do not cost money (no tokens used)
3. Are deterministic (same mock output every time)
4. Still test the orchestration, validation, streaming, and database logic

**Mock data example:**

```python
MOCK_EXTRACTION = ExtractionResult(
    core_facts=[
        "John Kamau entered into a sale agreement with Sarah Wanjiru on 01 March 2023",
        "The subject of the agreement was a parcel of land located in Kiambu County",
        ...
    ],
    entities=[
        Entity(name="John Kamau", type="person", role="plaintiff"),
        ...
    ],
    chronological_timeline=[
        TimelineEvent(date="2023-03-01", event="Sale agreement signed"),
        ...
    ]
)
```

**`collect_sse` helper:**

```python
async def collect_sse(response) -> list[dict]:
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events
```

This reads the entire SSE stream from a test response and returns all events as a list. Tests can then assert on specific events.

### `tests/test_analyze.py` (summary)

**File:** [backend/tests/test_analyze.py](../backend/tests/test_analyze.py)

Full per-test inventory is in **Section 21 → “Understanding What Each Test Does”** (regenerated from `pytest --collect-only`, **45** tests). At a high level the file covers: multipart **422** validation, SSE **`markdown_section` + `complete`** shape, per-step Markdown/DB assertions, **`mock_agents` wiring**, pipeline **failure** / **QA non-fatal** behaviour, and **`DELETE /api/v1/cases/{id}`** authorization.

---

## 16. Complete End-to-End Data Flow

Here is exactly what happens from the moment a user clicks "Run Litigation Pipeline" to when the brief appears on screen:

```
USER ACTION: Click "Run Litigation Pipeline" on /dashboard/new-scan
     │
     ▼
FRONTEND (new-scan/page.tsx)
  1. Validate form inputs (title required, text or file required)
  2. Create AbortController
  3. Call postAnalyzeStream() in lib/api.ts
     │
     ▼
FRONTEND (lib/api.ts: postAnalyzeStream)
  4. Build FormData object (title + case_text + optional file)
  5. POST /api/v1/analyze with X-User-Id header
  6. Receive streaming response body, begin reading in a loop
     │
     ▼ (HTTP request travels to backend)
     │
BACKEND (main.py: request logger middleware)
  7. Log: "POST /api/v1/analyze started"
     │
     ▼
BACKEND (api/dependencies.py: get_current_user)
  8. Resolve caller: non-production may use `X-User-Id` (or `dev-user-001`); production requires `Authorization: Bearer` + Clerk JWKS validation
     │
     ▼
BACKEND (api/routes_analyze.py: analyze)
  9. Parse Form fields (title, case_text)
  10. If file uploaded: call extract_uploaded_file_text() → plain text
  11. Merge case_text + file text
  12. Validate not empty
  13. Create AnalyzePipelineInput Pydantic object
  14. Return StreamingResponse(run_pipeline(...), media_type="text/event-stream")
     │
     ▼
BACKEND (agents/orchestrator.py: run_pipeline) — YIELDS SSE STRINGS
  15. INSERT Case(status=PROCESSING) into DB, commit

  ── STEP 0: EXTRACTION ──────────────────────────────────────────────
  16. INSERT AgentStep(name="extraction", step_index=0, status=PROCESSING)
  17. Call run_extraction_agent(raw_case_text) inside asyncio.wait_for + retry on transient OpenAI errors
        │
        ▼
      (agents/extraction.py — instructor + ExtractionResult)
  18.   On success: UPDATE step COMPLETED + result JSON; yield markdown_section("extraction", …)
        On hard failure: mark step FAILED, re-raise → outer handler emits error SSE

     ──── FRONTEND RECEIVES markdown_section ────
     → Append section to UI state; <details> shows extraction output
     ────────────────────────────────────────────

  ── STEP 1: RAG RETRIEVAL (non-critical) ───────────────────────────
  19. INSERT AgentStep(name="rag_retrieval", step_index=1, status=PROCESSING)
  20. Call rag_retrieve(raw_case_text) with the same timeout/retry wrapper
        │
        ▼
      (rag/retriever.py → embeddings + Chroma query)
  21.   On success: persist {"chunks": [...]}; on exception: log warning, mark step FAILED, chunks=[]
  22.   Always yield markdown_section("rag_retrieval", …) — even when chunks=[] ("No precedents" copy)

  ── STEP 2: STRATEGY ────────────────────────────────────────────────
  23. INSERT AgentStep(name="strategy", step_index=2, status=PROCESSING)
  24. Call run_strategy_agent(extraction, chunks)
        │
        ▼
      (agents/strategy.py — instructor + StrategyResult)
  25.   Persist strategy JSON; yield markdown_section("strategy", …)

  ── STEP 3: DRAFTING ────────────────────────────────────────────────
  26. INSERT AgentStep(name="drafting", step_index=3, status=PROCESSING)
  27. Call run_drafting_agent(extraction, strategy)
        │
        ▼
      (agents/drafting.py)
  28.   Persist DraftingResult; yield markdown_section("drafting", …)

  ── STEP 4: QA (non-critical) ───────────────────────────────────────
  29. INSERT AgentStep(name="qa", step_index=4, status=PROCESSING)
  30. Call run_qa_agent(extraction, draft)  # full structured objects, not only Markdown
        │
        ▼
      (agents/qa.py — instructor + QAResult)
  31.   On success: persist QA JSON; yield markdown_section("qa", …)
        On failure: log warning, mark step FAILED, skip QA markdown — pipeline still completes

  ── PIPELINE COMPLETE ───────────────────────────────────────────────
  32. UPDATE Case(status=COMPLETED); yield {"type": "complete", "case_id": "<uuid>"}
      (If any critical step above raised: Case=FAILED and final SSE is {"type":"error","detail":…})

BACKEND (main.py: request logger middleware)
  33. Log request completion / duration

FRONTEND (lib/api.ts: postAnalyzeStream)
  34. Stream ends, reader loop exits
  35. setLoading(false)

USER SEES: Up to five streamed sections (QA may be absent if QA failed), then completion UI;
           brief is ready. User can save or open /dashboard/scans.
```

---

## 17. Key Design Decisions and Why They Were Made

### 1. Multi-Agent Pipeline vs. Single Prompt

**What was chosen:** Five specialised agents in sequence, each with a narrow task.

**Alternative:** One giant prompt that says "read this case and write me a complete legal brief."

**Why the pipeline approach?**
- Each agent can use a different model (cheaper `gpt-4o-mini` for simple extraction, more capable `gpt-4o` for reasoning)
- Intermediate outputs can be validated with Pydantic schemas before being passed to the next step
- Individual agents can be replaced or improved independently
- The structured intermediate outputs (ExtractionResult, StrategyResult) make the reasoning transparent and auditable
- If one step fails, you know exactly which one and why

---

### 2. Structured Output with `instructor` vs. Prompt Engineering Alone

**What was chosen:** `instructor` library with Pydantic response models.

**Alternative:** Ask the model to "return JSON" in the prompt, then `json.loads()` the output, and handle any parsing errors.

**Why `instructor`?**
- The Pydantic schema is automatically converted to a JSON schema and injected into the prompt
- If the model returns malformed JSON or missing fields, `instructor` automatically retries with an error description
- The validated Pydantic object is immediately usable in Python — no manual key lookups
- Schema documentation in the Pydantic models doubles as model instructions

---

### 3. SSE Streaming vs. Polling vs. Single Response

**What was chosen:** Server-Sent Events (SSE) streaming.

**Alternative 1:** Return a single response after all agents finish (30-60+ seconds of loading spinner).

**Alternative 2:** Long polling — the client repeatedly calls `GET /status/{case_id}` every second.

**Why SSE?**
- Each agent result (5-15 seconds of processing) appears immediately without waiting for all five
- No repeated HTTP connections (unlike polling)
- One-directional server→client (unlike WebSockets), which is simpler for this read-only streaming use case
- The `StreamingResponse` in FastAPI is trivially simple to implement

---

### 4. RAG with ChromaDB vs. Fine-Tuning vs. Prompt Injection

**What was chosen:** ChromaDB vector database with text-embedding-3-small embeddings.

**Alternative 1:** Fine-tune a model on Kenyan legal text.

**Alternative 2:** Include all relevant legal text in every prompt.

**Why RAG?**
- Fine-tuning is expensive and requires retraining when laws change
- Full-text injection would exceed context window limits and increase cost dramatically
- RAG is dynamic — adding new legal documents to `data/raw/` and re-running ingestion immediately makes them available
- ChromaDB is free, runs locally, and persists on disk

---

### 5. SQLite for Development, PostgreSQL for Production

**What was chosen:** `DATABASE_URL` in `.env` configures the database. SQLite default for local dev, PostgreSQL for production.

**Alternative:** Always use PostgreSQL even in development.

**Why the split?**
- SQLite requires zero setup — no Docker, no credentials, file-based. Newcomers can clone and run immediately.
- PostgreSQL provides concurrent write safety, better performance at scale, and full-text search features needed in production.
- The SQLAlchemy async engine abstracts the difference — the exact same Python code works with both. Only the `DATABASE_URL` changes.

---

### 6. `gpt-4o-mini` for Extraction and QA, `gpt-4o` for Strategy and Drafting

**What was chosen:** Cheaper model for simpler tasks, more capable model for complex tasks.

**Why?**
- Extraction is information retrieval — finding and formatting facts that are already in the text. This does not require deep reasoning.
- QA is pattern matching — looking for known failure modes like unsupported claims or inconsistencies. Also relatively mechanical.
- Strategy requires multi-step legal reasoning: mapping facts to statutes, predicting counterarguments, constructing a coherent argument chain.
- Drafting requires fluent, formally structured professional writing.
- Cost: `gpt-4o-mini` is ~10× cheaper per token than `gpt-4o`. Using it for two of five steps significantly reduces per-case cost.

---

### 7. Clerk for Authentication vs. Custom Auth

**What was chosen:** Clerk (third-party auth provider).

**Alternative:** Build JWT authentication with FastAPI-Users or custom code.

**Why Clerk?**
- Clerk handles user registration, email verification, password reset, MFA, and social logins out of the box
- The frontend integration is a few lines: `<ClerkProvider>`, `<SignIn>`, `<SignedIn>`, `<SignedOut>`
- JWTs are RS256-signed and validated by the backend via JWKS — a standard, secure approach
- Clerk's dashboard provides user management without building admin tools

---

### 8. Async SQLAlchemy vs. Synchronous SQLAlchemy

**What was chosen:** `sqlalchemy[asyncio]` with `aiosqlite` driver.

**Why?**
- FastAPI is built on async Python. If database calls block the thread, the event loop cannot handle other concurrent requests during those calls.
- With async SQLAlchemy, while one request is waiting for a database response, other requests can execute. This significantly improves throughput.
- The pipeline makes multiple sequential database writes per request (one per agent step). Synchronous calls would create a bottleneck.

---

### 9. Tenacity for Retries vs. Manual Try/Except

**What was chosen:** `tenacity` retry decorator on OpenAI calls.

**Alternative:** `for i in range(3): try: ... except RateLimitError: time.sleep(2**i)`

**Why tenacity?**
- The decorator is declarative and readable: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))`
- Handles edge cases like cancelling retries on non-retryable errors
- Integrates with logging — can log each retry attempt automatically
- Separates retry policy from business logic

---

## 18. Rubric Self-Assessment

The project is evaluated on four categories. Here is an honest assessment of where each criterion stands:

### Technical Depth (20%)

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Problem selection & scope | 4/5 | Kenya-specific legal domain, explicit constraints (jurisdiction, court level), clear AI framing |
| Architecture & design choices | 4/5 | Modular multi-layer architecture, documented trade-offs, intentional model selection |
| Prompt & model interaction quality | 4/5 | Few-shot prompting, persona assignment, instructor for structured output, version tracking |
| Orchestration & control flow | 4/5 | Sequential pipeline with branching (critical vs. non-critical steps), retries, error handling |

### Engineering Practices (20%)

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Code quality | 4/5 | Layered architecture (routes/serializers/agents/services), consistent naming, no monolithic files |
| Logging & error handling | 4/5 | structlog with JSON output, per-event structured logs, global exception handler, step-level error tracking |
| Unit/integration tests | 5/5 | **143** pytest tests with async client, DB isolation, orchestrator‑level mocks, RAG + schema coverage, CI coverage gate |
| Observability | 3/5 | Structured **structlog** logs (HTTP + LLM + pipeline); no dashboards or distributed tracing yet |

### Production Readiness (15%)

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Solution feasibility | 4/5 | Cost-conscious model selection, SQLite→Postgres path, Clerk for scalable auth |
| Evaluation strategy | 4/5 | **`golden_cases.json`** (**11** cases) + **`eval_extraction.py`** / **`eval_llm_judge.py`**; **`.github/workflows/evals.yml`** runs extraction eval on path‑filtered pushes to **`main`** (**`continue-on-error: true`** → informational unless **`OPENAI_API_KEY`** is set and you remove that flag). LLM judge: **manual** workflow only (~$0.30+). |
| Deployment | 4/5 | GitHub Actions (`backend-deploy.yml`) runs **ruff**, **mypy**, **pytest** + coverage floor; Docker/Render docs in README |
| User interface | 4/5 | Clean two-column layout, real-time streaming, collapsible sections, search, delete |
| Demo quality | 4/5 | Full end-to-end pipeline visible, real-time output, history view |

### Presentation (15%)

Communication score depends on the demo delivery. Use Section 19 below as your guide.

---

## 19. Demo Script — What to Show and Say

### Narrative Arc
> "Legal briefs take hours to prepare manually. We built a system where a Kenyan lawyer types raw case notes, and in about 60 seconds, gets a structured brief ready for review — with full traceability of every reasoning step."

### Step-by-Step Demo Flow

**Step 1 — Show the architecture (30 seconds)**
Point to the architecture diagram in the README. Say:
> "We have five specialised AI agents running in sequence. Each one has a narrow, well-defined job and hands its output to the next. This is better than one big prompt because each step can be validated, retried independently, and uses the right model for its task."

**Step 2 — Run a case (2-3 minutes)**
Navigate to `/dashboard/new-scan`. Use this sample case:

```
Title: Land Dispute — Kamau v Wanjiru

Case Notes:
John Kamau entered into a sale agreement with Sarah Wanjiru on 1 March 2023 for a 
parcel of land in Kiambu County measuring 0.5 acres, Parcel No. KMB/1234, for a 
consideration of KSh 3,500,000. Kamau paid the full purchase price by bank transfer 
on 5 March 2023. Wanjiru signed a transfer document on the same date. Kamau took 
possession of the land and began construction. On 15 June 2023, Wanjiru obtained 
a court injunction preventing Kamau from continuing construction, claiming the 
transfer was obtained through undue influence. Kamau denies any undue influence. 
Wanjiru has not returned any portion of the purchase price. Kamau seeks to have 
the injunction vacated and the transfer registered.
```

Click "Run Litigation Pipeline." As events stream in, narrate:
> "The first agent — Extraction — is identifying the legally relevant facts, the parties, and the timeline. It uses GPT-4o-mini with few-shot prompting to ensure consistent structured output..."
> 
> "Now RAG retrieval is searching our local ChromaDB database of Kenyan legal documents for precedents on land transfer and undue influence..."
>
> "Strategy is now running on GPT-4o — the more capable model — because this step requires real legal reasoning: which sections of the Land Registration Act apply? What are the counterarguments?..."
>
> "Drafting is generating the formal brief in Kenyan High Court format. This agent uses the full structured output from extraction and strategy..."
>
> "Finally, QA audits the brief for hallucinations and logical gaps..."

**Step 3 — Open the collapsible sections**
Open the Strategy and Drafting sections. Point to:
- The legal issues identified
- The Kenyan statute citations
- The counterargument section
- The QA risk level (should be LOW)

**Step 4 — Show case history (30 seconds)**
Navigate to `/dashboard/scans`. Show:
> "Every case is saved. The user can search by title, view the full output of any historical case, and delete cases they no longer need."

**Step 5 — Show a technical detail (30 seconds)**
If technical judges are present, open the terminal and show the structlog output from the pipeline run:
> "Every LLM call is logged with model, duration in milliseconds, and token counts — giving us full observability into model performance and cost."

### Anticipated Questions

**Q: What happens if the OpenAI API is down?**
> "The orchestrator uses Tenacity to retry on rate limits and connection errors with exponential backoff — up to 3 attempts. If a non-critical step like RAG or QA fails completely, the pipeline continues rather than crashing. The case is marked with the step's failure status in the database."

**Q: How does it handle Kenyan law specifically?**
> "Two ways: First, the prompts explicitly specify 'only use Kenyan law, prefer primary legislation, cite sections with Cap numbers.' Second, our RAG system retrieves excerpts from Kenyan statutes stored locally in ChromaDB. The strategy agent is explicitly instructed not to fabricate citations."

**Q: Could this be used in production?**
> "The architecture is production-ready: async SQLAlchemy for database concurrency, Clerk for scalable authentication, PostgreSQL as the production database, and a Dockerfile for containerised deployment. The main production consideration is the LLM cost per case — using gpt-4o-mini for simpler steps is already a cost optimisation."

**Q: How do you know the output is accurate?**
> "The QA agent provides a first pass — it checks for hallucinations, fabricated statutes, and logical gaps. We also built a golden test dataset of known cases with expected outputs for offline evaluation. Ultimately, this is designed as a *drafting assistant* — all output should be reviewed by a qualified advocate before filing."

**Q: Why not use LangChain?**
> "LangChain adds a significant abstraction layer that, for this pipeline, would reduce transparency and control. Our orchestrator is 200 lines of clear async Python. Every data transformation is explicit. We chose direct OpenAI SDK + instructor because it is simpler to debug, test, and reason about."

---

*This document was generated from a comprehensive code review of the agent-juris repository as of April 2026.*

---

## 20. How to Run the Code

### Prerequisites Checklist

Before running anything, make sure you have:

| Tool | Minimum version | How to check |
|------|----------------|--------------|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node --version` |
| `uv` (Python package manager) | any recent | `uv --version` |
| Docker Desktop | any | `docker --version` |
| Git | any | `git --version` |
| An OpenAI API key | — | platform.openai.com |

> **What is `uv`?** `uv` is a fast Python package manager (an alternative to `pip`). It reads `pyproject.toml` and creates a virtual environment automatically. If you do not have it: `curl -LsSf https://astral.sh/uv/install.sh | sh` on Mac/Linux, or `pip install uv`.

---

### Step 1 — Clone and enter the repo

```bash
git clone <repo-url>
cd agent-juris
```

---

### Step 2 — Configure environment variables

```bash
cd backend
cp .env.example .env
```

Now open `backend/.env` and fill in the required values:

```bash
# Required — pick ONE of these:
OPENAI_API_KEY=sk-...          # Your OpenAI key from platform.openai.com
# OR
OPENROUTER_API_KEY=sk-or-...   # Your OpenRouter key (gives access to many models)

# Optional — only needed if you want Clerk auth to work:
CLERK_JWKS_URL=https://your-clerk-domain.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://your-clerk-domain.clerk.accounts.dev

# Optional — change the model (default is gpt-4o):
MODEL=gpt-4o

# Optional — set to "development" locally (this enables the X-User-Id shortcut):
APP_ENV=development
```

> **If you don't have Clerk set up:** Leave `CLERK_JWKS_URL` and `CLERK_ISSUER` blank. Since `APP_ENV=development`, the backend will accept any `X-User-Id` header instead of validating a real JWT. The frontend will still show Clerk's login page, but you can call the API directly with `curl` or the test suite without any auth.

---

### Step 3 — Start PostgreSQL (for local dev with persistent data)

```bash
# From the repo root:
cd infra
docker compose up -d
```

This starts a PostgreSQL 16 database at `localhost:5432`. The data is stored in a Docker volume so it survives restarts.

**To use this database**, set `DATABASE_URL` in your `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/litigation
```

> **If you skip this step:** The backend defaults to a local SQLite file (`litigation.db`), which is fine for development and testing. No Docker needed for SQLite.

---

### Step 4 — Install backend dependencies

```bash
cd backend
uv sync
```

`uv sync` reads `pyproject.toml`, creates a `.venv` virtual environment inside `backend/`, and installs all Python packages listed under `[project.dependencies]`.

> **What does this install?** FastAPI, SQLAlchemy, Pydantic, OpenAI SDK, instructor, structlog, tenacity, ChromaDB, pypdf, PyJWT, httpx, uvicorn, and all their transitive dependencies.

---

### Step 5 — Build the RAG knowledge base (one-time setup)

The RAG system needs Kenyan legal documents to be embedded and stored in ChromaDB before the backend can retrieve them.

```bash
cd backend
uv run python -m src.rag.ingestion
```

**What this does:**
1. Reads all `.txt` and `.md` files from `data/raw/`
2. Splits each document into 800-character overlapping chunks
3. Calls the OpenAI embeddings API to convert each chunk to a 1536-dimensional vector
4. Writes everything to `data/vector_db/` (ChromaDB files)

> **Note:** This makes real OpenAI API calls (roughly 1 call per 50 chunks). With the default dataset it costs a few cents. You only need to run this once unless you add new legal documents to `data/raw/`.

**Expected output:**
```
{"event": "rag_ingestion_complete", "files_processed": 3, "chunks_added": 42, ...}
```

---

### Step 6 — Start the backend server

```bash
cd backend
uv run uvicorn src.main:app --reload --port 8000
```

**Breaking this command down:**
- `uv run` — run inside the `.venv` virtual environment
- `uvicorn` — the ASGI server (like `node` for Python async apps)
- `src.main:app` — import `app` from `src/main.py`
- `--reload` — automatically restart the server when you change a Python file (dev only)
- `--port 8000` — listen on port 8000

**Expected startup output (development mode):**
```
[structlog] configure_logging → console mode
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Verify it is working:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

---

### Step 7 — Install frontend dependencies

```bash
cd frontend
npm install
```

This reads `package.json` and installs Next.js, React, Clerk, react-markdown, and all other JavaScript packages into `frontend/node_modules/`.

---

### Step 8 — Configure the frontend environment

```bash
cd frontend
cp .env.local.example .env.local   # if this file exists, otherwise create it
```

Create `frontend/.env.local` with:
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

# Clerk publishable key (get from Clerk dashboard → API Keys):
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Clerk secret key (get from Clerk dashboard → API Keys):
CLERK_SECRET_KEY=sk_test_...
```

> **If you don't have Clerk:** You can still call the backend API directly (with curl or the test suite). The frontend will show the Clerk login page and you will not be able to log in, but the backend works independently.

---

### Step 9 — Start the frontend

```bash
cd frontend
npm run dev
```

**Expected output:**
```
  ▲ Next.js 16.x.x (Turbopack)
  - Local:        http://localhost:3000
  - Ready in 847ms
```

Open `http://localhost:3000` in your browser. You will see the landing page.

---

### Quick Reference — All Commands at Once

```bash
# Terminal 1: Database (optional, SQLite works without it)
cd infra && docker compose up -d

# Terminal 2: Backend
cd backend
cp .env.example .env          # fill in OPENAI_API_KEY
uv sync
uv run python -m src.rag.ingestion   # one-time RAG setup
uv run uvicorn src.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000.

---

### Calling the API Directly (Without the Frontend)

You can test the backend with `curl`. In development mode, use `X-User-Id` header for authentication:

```bash
# Health check
curl http://localhost:8000/health

# Who am I?
curl -H "X-User-Id: my-test-user" http://localhost:8000/api/v1/me

# Run the pipeline (streaming response)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-User-Id: my-test-user" \
  -F "title=Test Case" \
  -F "case_text=John sued Sarah for breach of contract in Nairobi." \
  --no-buffer

# List cases
curl -H "X-User-Id: my-test-user" http://localhost:8000/api/v1/cases
```

---

## 21. How to Run the Tests

The test suite is in `backend/tests/` and uses **pytest** with **pytest-asyncio**. All tests run completely offline — no real OpenAI API calls, no network, no cost.

### Install dev dependencies

```bash
cd backend
uv sync --all-extras   # installs pytest, pytest-asyncio, pytest-cov, etc.
```

---

### Run all tests

```bash
cd backend
uv run pytest
```

**Expected output:**
```
========================= test session starts ==========================
platform darwin -- Python 3.12.x, pytest-8.x.x, pluggy-1.x.x
asyncio_mode: auto
collected 143 items

tests/test_health.py ...                                          [  2%]
tests/test_me.py .....                                            [  6%]
tests/test_schemas.py ............................                 [ 30%]
tests/test_rag.py ..............................                   [ 55%]
tests/test_analyze.py ...............................               [ 80%]
tests/test_history.py .......................                       [100%]

========================= 143 passed in ~6s ==========================
```

---

### Run with coverage report

```bash
cd backend
uv run pytest --cov=src --cov-report=term-missing
```

This shows which lines of `src/` are covered by tests. Lines marked as "missing" are not tested.

---

### Run a specific test file

```bash
uv run pytest tests/test_analyze.py           # just the analyze tests
uv run pytest tests/test_analyze.py -v        # verbose (prints each test name)
uv run pytest tests/test_analyze.py::test_pipeline_returns_200_with_event_stream  # one test
```

---

### Run with a keyword filter

```bash
uv run pytest -k "error"       # run all tests whose name contains "error"
uv run pytest -k "rag"         # run all RAG-related tests
uv run pytest -k "isolation"   # run all user-isolation tests
```

---

### Understanding What Each Test Does

Below is **every automated test** (143 total) in plain English, grouped by file. Names match `pytest -v` / `pytest --collect-only -q`. If you add tests, refresh this subsection and the maintenance banner at the top of the doc.

---

#### `tests/test_health.py` — Basic Liveness (3 tests)

These are the simplest tests. They check that the server is alive and the health endpoint works.

| Test name | What it checks | What "pass" means |
|-----------|---------------|-------------------|
| `test_health_returns_ok` | GET /health → 200, body is `{"status": "ok"}` | Server starts and basic routing works |
| `test_health_requires_no_auth` | GET /health without any auth header → 200 | Health check is publicly accessible (no auth needed for monitoring) |
| `test_health_content_type_is_json` | Response Content-Type contains `application/json` | Clients can safely parse the response as JSON |

**Why these matter for the demo:** If the server has crashed, `test_health_returns_ok` fails immediately. This is your first line of defence.

---

#### `tests/test_me.py` — `GET /api/v1/me` (5 tests)

These exercise the **development** path (`Authorization` omitted → `X-User-Id` or default `dev-user-001`). When `settings.app_env == "production"`, callers must send **`Authorization: Bearer …`** and **`get_current_user`** validates **Clerk JWTs** via JWKS (`src/api/dependencies.py`).

| Test name | What it checks | What "pass" means |
|-----------|---------------|-------------------|
| `test_me_default_user_when_no_header` | No header → returns `dev-user-001` | Dev fallback works; server doesn't crash when no auth is provided |
| `test_me_reflects_custom_user_id` | `X-User-Id: alice-test` → response has `user_id: "alice-test"` | The header is correctly read and passed through |
| `test_me_response_has_user_id_key` | Response body contains a `user_id` key | Frontend can always extract the user ID safely |
| `test_me_email_is_null_by_default` | Email field is `null` in dev mode | Clerk integration is optional; null is a safe default |
| `test_me_different_users_return_different_ids` | Alice and Bob get different `user_id` values | Auth identity is not accidentally shared between requests |

**Why these matter:** They lock in the **`CurrentUser`** contract the rest of the app relies on (stable `user_id`, header passthrough, safe defaults). **Clerk JWT validation** lives in `get_current_user` and is covered indirectly when running against real tokens; this file intentionally stays on the fast **`X-User-Id`** stub used in CI.

---

#### `tests/test_schemas.py` — Pydantic schema validation (26 tests)

Pure unit tests — no HTTP, database, or agents. They prove each **`ai_schemas`** model accepts the shapes produced by prompts and rejects drift.

**Entity (4 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_entity_accepts_all_improved_types` | All eight `type` literals (person, company, government_body, place, document, court, contract, statute) validate |
| `test_entity_requires_name` | Missing `name` → `ValidationError` |
| `test_entity_requires_type` | Missing `type` → `ValidationError` |
| `test_entity_requires_role` | Missing `role` → `ValidationError` |

**TimelineEvent (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_timeline_event_accepts_iso_date` | ISO-style date string accepted |
| `test_timeline_event_accepts_unknown_date` | Literal `"unknown"` accepted for undated events |
| `test_timeline_event_requires_both_fields` | Both `date` and `event` required |

**ExtractionResult (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_extraction_result_valid` | Full object with `core_facts`, `entities`, `chronological_timeline` accepted |
| `test_extraction_result_empty_lists_are_valid` | Empty lists allowed (density is prompt-level, not schema-level) |
| `test_extraction_result_requires_all_three_fields` | Omitting any list field → `ValidationError` |

**LegalArgument (2 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_legal_argument_valid` | `issue`, `applicable_kenyan_law`, `argument_summary` together form a valid nested argument |
| `test_legal_argument_requires_all_fields` | Omitting `argument_summary` (or other required field) → `ValidationError` |

**Counterargument (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_counterargument_valid` | Paired `rebutting_argument` / `counterargument` strings validate |
| `test_counterargument_requires_both_fields` | Either side missing → `ValidationError` |
| `test_counterargument_fields_must_be_strings` | Non-string values → `ValidationError` |

**StrategyResult (4 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_strategy_result_valid_with_structured_counterarguments` | Full strategy object with `LegalArgument` and `Counterargument` children accepted |
| `test_strategy_result_counterarguments_must_be_counterargument_objects` | Plain strings in `counterarguments` list → `ValidationError` (guards the pre-refactor wire format) |
| `test_strategy_result_serialises_counterarguments_as_dicts` | `model_dump()` nests counterarguments as plain dicts suitable for JSON round-trip |
| `test_strategy_result_requires_all_fields` | Partial construction → `ValidationError` |

**DraftingResult (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_drafting_result_accepts_any_nonempty_markdown` | Any non-empty `brief_markdown` string validates |
| `test_drafting_result_requires_brief_markdown` | Missing field → `ValidationError` |
| `test_drafting_result_accepts_empty_string` | Empty string allowed on the model (full brief structure enforced downstream / by prompts) |

**QAResult (4 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_qa_result_valid_low_risk` | LOW risk with empty list fields validates |
| `test_qa_result_valid_high_risk` | HIGH risk with populated warnings validates |
| `test_qa_result_requires_all_four_fields` | All scalar and list slots required |
| `test_qa_result_all_list_fields_are_lists` | List-typed fields reject non-lists |

**Why these matter for the rubric:** They document the *contract* between structured LLM output and Python types. A silent schema mismatch becomes a failing test instead of a bad row in `agent_steps`.

---

#### `tests/test_rag.py` — RAG System (38 tests)

Split into four groups:

**Group 1: `chunk_text` unit tests (11 tests)**

These test the text-splitting function in isolation — no AI, no network.

| Test name | What it checks |
|-----------|---------------|
| `test_chunk_text_empty_string_returns_empty_list` | Empty input → empty list |
| `test_chunk_text_whitespace_only_returns_empty_list` | Whitespace-only input → empty list (important edge case) |
| `test_chunk_text_short_text_returns_single_chunk` | Text shorter than chunk size → exactly one chunk |
| `test_chunk_text_long_text_produces_multiple_chunks` | Text longer than chunk size → multiple chunks |
| `test_chunk_text_no_chunk_exceeds_size` | No chunk is longer than CHUNK_SIZE characters |
| `test_chunk_text_all_chunks_non_empty` | No empty chunks are produced (stripping whitespace works) |
| `test_chunk_text_exactly_chunk_size_returns_one_chunk` | Text of exactly CHUNK_SIZE → one chunk |
| `test_chunk_text_zero_overlap_produces_non_overlapping_chunks` | With overlap=0, 300 chars / 100 per chunk = exactly 3 chunks |
| `test_chunk_text_overlap_tail_of_first_matches_head_of_second` | The last 20 chars of chunk[0] equal the first 20 chars of chunk[1] |
| `test_chunk_text_strips_leading_trailing_whitespace_from_each_chunk` | Each chunk has no leading/trailing whitespace |
| `test_chunk_text_full_coverage_no_content_lost` | With zero overlap, all content is preserved across all chunks |

**Group 2: `rag_retrieve` unit tests (10 tests)**

These mock both the OpenAI embeddings API and ChromaDB to test the retriever in isolation.

| Test name | What it checks |
|-----------|---------------|
| `test_rag_retrieve_returns_list_of_strings` | Result is a list where every element is a string |
| `test_rag_retrieve_returns_correct_chunk_content` | Exact text from ChromaDB is returned unchanged |
| `test_rag_retrieve_empty_collection_returns_empty_list` | If ChromaDB has no documents, returns [] without querying |
| `test_rag_retrieve_empty_query_returns_empty_list_no_openai_call` | Empty query → [] immediately, no embedding call made |
| `test_rag_retrieve_whitespace_query_returns_empty_list` | Whitespace-only query → [], no embedding call |
| `test_rag_retrieve_passes_correct_embedding_to_chroma` | The exact embedding vector returned by OpenAI is passed to ChromaDB |
| `test_rag_retrieve_respects_n_results_argument` | Custom `n_results` is passed through to ChromaDB |
| `test_rag_retrieve_caps_n_results_at_collection_size` | If you request 10 results but only 2 documents exist, query uses n_results=2 |
| `test_rag_retrieve_filters_out_empty_document_strings` | Empty strings in ChromaDB results are filtered out |
| `test_rag_retrieve_uses_documents_include_parameter` | ChromaDB is called with `include=["documents"]` (not embeddings or metadata) |

**Group 3: `ingest_documents` tests (8 tests)**

These test the ingestion script that builds the vector database.

| Test name | What it checks |
|-----------|---------------|
| `test_ingest_documents_empty_directory_returns_no_files_found` | Empty `data/raw/` → `{"detail": "no_files_found", "chunks_added": 0}` |
| `test_ingest_documents_success_returns_ok_with_chunk_count` | With real files → `{"detail": "ok", "chunks_added": N}` where N > 0 |
| `test_ingest_documents_calls_collection_add_exactly_once` | ChromaDB's `add()` is called exactly once (batching works) |
| `test_ingest_documents_add_receives_matching_docs_ids_embeddings` | The counts of documents, IDs, embeddings, and metadata all match |
| `test_ingest_documents_chunk_ids_are_all_unique` | All chunk UUIDs are unique (no duplicate IDs) |
| `test_ingest_documents_metadata_records_source_filename` | Each chunk's metadata includes its source filename |
| `test_ingest_documents_total_embeddings_match_chunks_embedded` | The number of embeddings requested from OpenAI equals chunks_added |
| `test_ingest_documents_accepts_markdown_files` | `.md` files (not just `.txt`) are ingested correctly |

**Group 4: Pipeline integration tests (9 tests)**

These test that RAG chunks flow correctly through the full pipeline.

| Test name | What it checks |
|-----------|---------------|
| `test_strategy_receives_rag_chunks_as_second_argument` | When RAG returns chunks, they are passed as the 2nd arg to the strategy agent |
| `test_strategy_receives_empty_list_when_rag_returns_nothing` | RAG returning [] → strategy gets `[]`, not `None` |
| `test_rag_retrieval_sse_section_reflects_non_empty_chunks` | Non-empty RAG results appear in the `rag_retrieval` SSE section markdown |
| `test_rag_retrieval_sse_section_shows_no_precedents_when_empty` | Empty RAG results → "No precedents" in the SSE section markdown |
| `test_rag_step_stored_in_db_with_correct_chunks` | The RAG chunks are persisted in the `agent_steps` table result column |
| `test_rag_step_stored_in_db_with_empty_chunks` | Empty RAG result stored as `{"chunks": []}` in DB |
| `test_pipeline_completes_successfully_with_non_empty_rag` | Full pipeline reaches `complete` event even when RAG returns data |
| `test_rag_step_status_is_completed_in_db` | The `rag_retrieval` step shows `COMPLETED` status in the DB |
| `test_rag_step_index_is_1` | The `rag_retrieval` step has `step_index = 1` (second step) |

---

#### `tests/test_analyze.py` — Core Pipeline Endpoint (45 tests)

This is the largest and most important test file. It tests the `POST /api/v1/analyze` endpoint end-to-end.

**Input validation tests (8 tests):**

| Test name | What it checks | Why it matters |
|-----------|---------------|----------------|
| `test_blank_title_returns_422` | `title=""` → HTTP 422 | Users cannot submit untitled cases |
| `test_whitespace_title_returns_422` | `title="  \t "` → HTTP 422 | Whitespace-only is treated as blank (`.strip()` logic works) |
| `test_missing_title_returns_422` | No `title` field at all → HTTP 422 | FastAPI's Form validation works |
| `test_no_case_text_and_no_file_returns_422` | `case_text=""`, no file → HTTP 422 | Must have at least one source of case content |
| `test_whitespace_only_case_text_returns_422` | `case_text="   \n\t  "` → HTTP 422 | Whitespace-only text is useless content |
| `test_json_body_instead_of_form_returns_422` | JSON body instead of form data → HTTP 422 | Confirms the endpoint only accepts multipart/form-data |
| `test_invalid_body_returns_422` | Raw bytes with wrong content-type → HTTP 422 | Malformed requests are rejected cleanly |
| `test_extra_form_fields_are_ignored` | Extra form field `unknown_field` → HTTP 200 | Unknown fields do not crash the API (forwards-compatible) |

**SSE envelope and ordering (8 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_pipeline_returns_200_with_event_stream` | Status 200, `Content-Type` contains `text/event-stream` |
| `test_pipeline_emits_five_markdown_sections_plus_complete` | Stream ends with five `markdown_section` events plus one `complete` |
| `test_last_event_is_complete` | Final event has `type: "complete"` |
| `test_final_event_contains_case_id` | `complete` payload includes `case_id` |
| `test_case_id_is_valid_uuid` | `case_id` parses as a UUID |
| `test_markdown_sections_arrive_in_correct_order` | Section IDs: `extraction` → `rag_retrieval` → `strategy` → `drafting` → `qa` |
| `test_each_markdown_section_has_heading_and_body` | Every `markdown_section` has non-empty `markdown` with a heading line |
| `test_section_indices_match_step_order` | `step_index` on each section follows pipeline order |

**Per-step Markdown, persistence, and shape (17 tests)**

These assert both the **SSE markdown** and, where relevant, the **`agent_steps` JSON** saved for extraction, strategy, drafting, and QA.

| Test name | What it checks |
|-----------|---------------|
| `test_extraction_markdown_contains_structure` | Extraction section has `### Core facts` and `### Entities` headings, and contains "John Kamau" |
| `test_rag_markdown_when_empty_chunks` | When RAG returns [], the section contains "No precedents" |
| `test_strategy_markdown_contains_issues_and_laws` | Strategy section has `### Legal issues`, `### Applicable laws`, and contains "Law of Contract Act" |
| `test_strategy_counterarguments_rendered_in_markdown` | Strategy section has `### Counterarguments` with rebutting argument and "void" text |
| `test_strategy_arguments_rendered_in_markdown` | Strategy section has `### Arguments` with "Law of Contract Act" |
| `test_strategy_counterarguments_are_structured_objects` | DB step result contains counterarguments as dicts with `rebutting_argument` and `counterargument` keys |
| `test_strategy_arguments_are_structured_objects` | DB step result contains arguments as dicts with `issue`, `applicable_kenyan_law`, `argument_summary` keys |
| `test_drafting_result_has_brief_markdown` | Drafting section markdown starts with `# IN THE MATTER OF` |
| `test_drafting_brief_contains_required_sections` | Brief markdown contains all 5 required section headers |
| `test_drafting_brief_persisted_with_required_sections` | Same check on the DB-persisted version of the brief |
| `test_qa_result_has_required_keys` | QA section contains "LOW" (risk level) |
| `test_qa_result_has_all_output_fields` | QA section has `### Hallucination warnings`, `### Missing logic`, `### Risk notes` |
| `test_qa_result_persisted_with_all_schema_fields` | DB result has all four QA fields including lists |
| `test_extraction_markdown_entities_contain_name` | "John Kamau" and "Sarah Wanjiru" appear in the extraction markdown |
| `test_extraction_markdown_timeline_present` | Extraction has `### Chronological timeline` section |
| `test_extraction_entities_have_name_type_role` | Every entity in DB result has name, type, and role string fields |
| `test_extraction_timeline_events_have_date_and_event` | Every timeline entry in DB result has date and event string fields |

**Mock call wiring (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_each_agent_called_exactly_once` | Extraction, RAG, strategy, drafting, and QA mocks each invoked exactly once |
| `test_strategy_receives_extraction_output` | Strategy mock's first positional arg is `MOCK_EXTRACTION` |
| `test_drafting_receives_extraction_and_strategy` | Drafting mock receives `MOCK_EXTRACTION` then `MOCK_STRATEGY` |

**Pipeline failures, SSE errors, and recovery (6 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_extraction_failure_emits_error_event` | Extraction `RuntimeError` → stream ends with `type: "error"` and detail text mentioning the failure (fixture uses a rate-limit message) |
| `test_mid_pipeline_failure_emits_markdown_for_prior_steps_only` | Strategy raises → only `extraction` and `rag_retrieval` markdown sections appear before the error |
| `test_qa_failure_does_not_abort_pipeline` | QA raises → no `qa` markdown section, but stream still ends with `complete` |
| `test_failed_case_saved_with_failed_status` | Failed run still inserts a case row with `status: "FAILED"` |
| `test_server_continues_serving_after_pipeline_error` | After a failed analyze, `GET /health` still returns 200 |
| `test_error_event_contains_detail_string` | Terminal `error` event carries a non-empty string `detail` |

**`DELETE /api/v1/cases/{id}` authorization (3 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_delete_case_returns_204` | Owner delete → **204 No Content** |
| `test_delete_case_removes_from_history` | After delete, `GET /api/v1/cases` no longer lists that `id` |
| `test_delete_other_users_case_returns_404` | Non-owner delete → **404** and row unchanged for the owner |

---

#### `tests/test_history.py` — Case History Management (26 tests)

These test the case list and detail endpoints.

**Empty state tests (2 tests):**

| Test name | What it checks |
|-----------|---------------|
| `test_history_empty_for_brand_new_user` | New user's GET /cases returns `[]` |
| `test_history_empty_for_user_with_no_cases` | User B gets `[]` even when User A has cases |

**After a successful analysis (5 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_history_has_one_entry_after_analyze` | One completed run → exactly one list row |
| `test_history_entry_status_is_completed` | Row `status` is `COMPLETED` |
| `test_history_entry_has_required_fields` | Row exposes `id`, `title`, `raw_input`, `status`, `created_at` |
| `test_history_entry_raw_input_matches_submitted_text` | `raw_input` equals submitted case text |
| `test_history_accumulates_multiple_cases` | Two runs → two distinct rows |

**Ordering (1 test)**

| Test name | What it checks |
|-----------|---------------|
| `test_history_most_recent_case_first` | Newest `created_at` appears first in `GET /api/v1/cases` |

**User isolation tests (3 tests) — Critical security tests:**

| Test name | What it checks |
|-----------|---------------|
| `test_user_a_cannot_see_user_b_cases` | User A's list is empty when only User B has cases |
| `test_each_user_sees_only_their_own_cases` | With cases for both A and B, each user sees exactly 1 |
| `test_user_isolation_by_case_id` | User B gets 404 when requesting User A's case by ID directly |

> **Why isolation tests are critical:** This is a multi-tenant application. If these tests failed, any user could see any other user's legal cases — a serious data breach. These tests are your proof that the ownership check in the SQL queries works.

**Detail, search, delete, and step payloads (14 tests)**

| Test name | What it checks |
|-----------|---------------|
| `test_case_detail_returns_200` | Owner `GET /api/v1/cases/{id}` → 200 |
| `test_case_detail_includes_title` | Detail JSON includes expected `title` |
| `test_list_cases_search_by_title_substring` | `GET /api/v1/cases?q=…` filters by title substring |
| `test_list_cases_title_search_no_match_returns_empty` | Query with no hits → `[]` |
| `test_delete_case_returns_204_and_removes` | Owner delete → 204 and row disappears from list |
| `test_delete_case_cross_user_returns_404` | Other user cannot delete; owner still sees the case |
| `test_case_detail_nonexistent_id_returns_404` | Unknown UUID → 404 |
| `test_case_detail_has_5_agent_steps` | Detail embeds five `agent_steps` |
| `test_case_detail_step_names_are_correct` | Step names match pipeline order (`extraction` … `qa`) |
| `test_case_detail_steps_ordered_by_index` | `step_index` values are contiguous starting at 0 |
| `test_case_detail_all_steps_are_completed` | Each step `status` is `COMPLETED` for happy path |
| `test_case_detail_all_steps_have_result` | Every step has a non-null `result` blob |
| `test_case_detail_extraction_step_shape` | Extraction JSON includes facts, entities, timeline keys |
| `test_case_detail_drafting_step_has_brief_markdown` | Drafting JSON includes non-empty `brief_markdown` |

**Failed case persistence (1 test):**

| Test name | What it checks |
|-----------|---------------|
| `test_failed_case_appears_in_history` | A crashed pipeline → case in history with `status: "FAILED"` (not invisible) |

---

### How to Interpret Test Results

**All tests pass:**
```
143 passed in ~6s
```
The codebase is in a working state. The contracts between all layers are honoured.

**Some tests fail:**
```
FAILED tests/test_analyze.py::test_drafting_brief_contains_required_sections
```
This means the `format_markdown.py` converter or the mock brief structure no longer matches what the test expects. Read the assertion error message — it will say exactly which section heading is missing.

**An error (not a failure):**
```
ERROR tests/test_history.py::test_history_has_one_entry_after_analyze
```
An error means the test itself crashed (e.g., an import failed, a fixture broke) rather than an assertion failing. Check for import errors or missing dependencies first.

---

## 22. Evals, Monitoring, and Logging — The Full Picture

This section explains the three quality assurance layers in the project and maps each one against the rubric.

---

### Layer 1 — Structured Logging (Engineering Practices: Logging & Error Handling)

**File:** [backend/src/core/logging.py](../backend/src/core/logging.py)

The project uses **structlog** for all logging. Every log line is a structured event with key-value pairs, not a plain text string.

**How logging works in each agent:**

```python
# From extraction.py — before the LLM call:
logger.info(
    "llm_call_start",
    step="extraction",
    model="gpt-4o-mini",
    prompt_version=PROMPT_VERSION,
)

# After the call completes:
logger.info(
    "llm_call_complete",
    step="extraction",
    model="gpt-4o-mini",
    duration_ms=round((time.monotonic() - t0) * 1000),
    prompt_tokens=response.usage.prompt_tokens,
    completion_tokens=response.usage.completion_tokens,
)
```

**Development output** (human-readable console):
```
2026-04-22T10:30:01Z [info     ] llm_call_start    step=extraction model=gpt-4o-mini prompt_version=v1.1
2026-04-22T10:30:03Z [info     ] llm_call_complete step=extraction model=gpt-4o-mini duration_ms=1823 prompt_tokens=450 completion_tokens=312
```

**Production output** (newline-delimited JSON):
```json
{"event": "llm_call_start", "step": "extraction", "model": "gpt-4o-mini", "timestamp": "2026-04-22T10:30:01Z", "level": "info"}
{"event": "llm_call_complete", "step": "extraction", "model": "gpt-4o-mini", "duration_ms": 1823, "prompt_tokens": 450, "completion_tokens": 312, "timestamp": "2026-04-22T10:30:03Z", "level": "info"}
```

**Complete list of logged events across the codebase:**

| Event name | Where | Key fields |
|------------|-------|------------|
| `pipeline_start` | orchestrator.py | `case_id`, `user_id`, `title` |
| `step_complete` | orchestrator.py | `case_id`, `step` |
| `rag_retrieval_failed` | orchestrator.py | `case_id`, `reason` |
| `qa_step_failed` | orchestrator.py | `case_id`, `reason` |
| `pipeline_complete` | orchestrator.py | `case_id` |
| `pipeline_failed` | orchestrator.py | `case_id`, `reason` (+ full traceback) |
| `llm_call_start` | extraction/strategy/drafting/qa | `step`, `model`, `prompt_version` (extraction only) |
| `llm_call_complete` | extraction/strategy/drafting/qa | `step`, `model`, `duration_ms`, `prompt_tokens`, `completion_tokens` |
| `rag_embed_start` | retriever.py | `query_length` |
| `rag_embed_complete` | retriever.py | `duration_ms` |
| `rag_collection_empty` | retriever.py | (warning — no documents in ChromaDB) |
| `rag_retrieve_complete` | retriever.py | `chunks_returned` |
| HTTP request log | main.py middleware | `method`, `path`, `status_code`, `duration_ms` |

**What you can ask from these logs in production:**
- "How long does the strategy step take on average?" → filter `event=llm_call_complete AND step=strategy`, average `duration_ms`
- "How many tokens are we spending per case?" → sum `prompt_tokens + completion_tokens` per `case_id`
- "How often does RAG return no results?" → count `event=rag_collection_empty`
- "How often does the pipeline fail?" → count `event=pipeline_failed`

**Rubric mapping:** The structured logging with levels (info/warning), per-event context fields, and production JSON output maps to **score 4 ("Structured logging with levels, errors surface meaningful context")** on the Engineering Practices: Logging & Error Handling criterion.

**What is missing for score 5:** A full observability stack would add distributed tracing (OpenTelemetry spans linking HTTP request → pipeline steps → LLM calls), alerting rules (PagerDuty alert if pipeline failure rate > 5%), and a dashboard (Grafana/Datadog) showing token spend and p95 latency by step.

---

### Layer 2 — Unit and Integration Tests (Engineering Practices: Unit/Integration Tests)

The test suite is described fully in Section 21. Here is the rubric mapping:

| What exists | Evidence | Rubric score contribution |
|-------------|----------|--------------------------|
| 143 tests across 6 files | All pass with `uv run pytest` | Not trivial (score 2+) |
| Tests for every pipeline step | test_analyze.py checks each agent's output shape | Core logic tested (score 3) |
| Well-named tests with clear assertions | Each test name describes exactly what it checks | Good coverage (score 3-4) |
| Mocked agents eliminate API cost/flakiness | `mock_agents` fixture patches at orchestrator level | Repeatable (score 4) |
| Tests for error paths (QA non-critical, mid-failure) | Error handling tests in test_analyze.py | Failure modes tested (score 4) |
| Integration tests (pipeline → DB → history endpoint) | `run_analyze()` helper + GET /cases/{id} assertions | Integration coverage (score 4) |
| User isolation security tests | `test_user_isolation_by_case_id`, `test_each_user_sees_only_their_own_cases` | Security coverage |
| Schema validation tests | test_schemas.py | Contract tested |

**What is missing for score 5:**
- Broader CI matrix (e.g. multiple Python versions or **`pull_request`** triggers on every branch) — **`backend-deploy.yml`** already runs **pytest** + coverage on pushes
- Tests for the RAG ingestion edge cases with real files (currently mocked)
- Tests for the file upload service (PDF extraction)
- Load/concurrency tests (what happens with 10 simultaneous pipeline requests?)

---

### Layer 3 — Evaluations (Production Readiness: Evaluation Strategy)

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). Details in the **`evals.yml`** table and rubric rows **later in this section**.

The project has two separate evaluation scripts in `backend/evals/`. These are distinct from tests — they make **real OpenAI API calls** against **golden case texts** to measure output quality.

---

#### GitHub Actions — `.github/workflows/evals.yml`

| Job | When it runs | Merge gate? | Notes |
|-----|----------------|---------------|--------|
| **`extraction-eval`** | Push to **`main`** when `backend/src/agents/**`, `backend/evals/**`, `backend/data/raw/**`, or this workflow file changes | **No** (job uses **`continue-on-error: true`**) | Runs **`uv run python -m evals.eval_extraction`** against **all** rows in **`golden_cases.json`** (**11** cases). Pass/fail is visible in the Actions log. Without **`OPENAI_API_KEY`** in repo secrets the step fails at OpenAI — the workflow still shows green overall. Remove **`continue-on-error`** (and add the secret) to make failures block merges. |
| **`llm-judge`** | Only **Actions → Evaluations → Run workflow** with **“Also run LLM-as-judge eval”** checked | N/A (manual) | Runs **`eval_llm_judge`** with **`--threshold 3.0`**. Expensive (~**$0.30+** per run); intended before release or when auditing brief quality. |

---

#### Eval 1: Extraction Golden Cases — `evals/eval_extraction.py`

**What it does:** Runs the real extraction agent against **every** case in **`golden_cases.json`** (**11** scenarios covering multiple domains) and checks each output against that case’s **`expected`** constraints.

**Sample golden cases** (full list is in the JSON file):

| Case ID | Description | What it tests |
|---------|-------------|---------------|
| `land-001` | John Kamau v Sarah Wanjiru — land sale, specific performance | Contract facts, person/place entities, ISO date handling |
| `supply-001` | Wanjiru Holdings v Nairobi County Government — unpaid supply | Company/government entities, multi-event timeline, procurement keywords |
| `employment-001` | Grace Muthoni v Apex Developers — unfair dismissal | Person/company entities, disciplinary keywords, salary facts |

**What is checked per case:**

```json
{
  "min_core_facts": 4,                          // Must extract at least 4 facts
  "required_entity_names": ["John Kamau", ...], // These names must appear
  "required_entity_types": ["person", "place"], // These entity types must appear
  "min_timeline_events": 2,                     // At least 2 timeline events
  "timeline_must_contain_date_prefix": "2023-03-15", // This date must be in timeline
  "expected_keywords_in_facts": ["KES 5,000,000", ...] // These words must be in facts
}
```

**How to run it:**

```bash
cd backend
uv run python -m evals.eval_extraction
```

**Expected output:**
```
Extraction eval — golden cases

  Running land-001: Land sale specific performance ... PASS
  Running supply-001: Government procurement ... PASS
  Running employment-001: Unfair termination ... PASS

Result: 11/11 passed
```

**If a case fails:**
```
  Running land-001: Land sale specific performance ... FAIL

Failures:
  - [land-001] core_facts: expected >= 4, got 2
  - [land-001] timeline missing event with date prefix '2023-03-15'; found: ['2023-03', 'unknown']
```

**Exit code:** Returns **0** on full pass, **1** on any failure — suitable for a **strict** CI gate when the workflow job does **not** use **`continue-on-error`**.

**Cost:** Roughly **~$0.05** per full extraction eval (**11** × **gpt-4o-mini** extraction calls), suitable for frequent automation once you accept API spend.

**CI behaviour today:** The **`extraction-eval`** job in **`evals.yml`** uses **`continue-on-error: true`**, so the workflow is **informational** (yellow step on failure) and does **not** block merges. Add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`** when you want failures to block **`main`**.

---

#### Eval 2: LLM-as-Judge — `evals/eval_llm_judge.py`

**What it does:** Runs the full pipeline on each golden case, then passes the generated brief to a **second GPT-4o instance** that scores it on three dimensions.

**The judge prompt scores each brief from 1–5 on:**
- **Completeness** (1–5): Does the brief address all material legal issues?
- **Factual grounding** (1–5): Is every claim traceable to the source facts? (Hallucination detection)
- **Actionability** (1–5): Does the brief give a Kenyan advocate clear next steps, specific statutes, and a prayer for relief?

A **composite score** = average of the three dimensions. The script passes if the mean composite score across all cases meets the threshold (default 3.0/5.0).

**How to run it:**

```bash
cd backend
uv run python -m evals.eval_llm_judge

# With a stricter threshold:
uv run python -m evals.eval_llm_judge --threshold 3.5
```

**Expected output:**
```
LLM-as-judge eval — full pipeline

  [land-001] Land sale specific performance
    completeness=4/5  factual_ground=5/5  actionability=4/5
    composite=4.33/5
    comment: Brief clearly identifies specific performance as the primary relief.

  [supply-001] Government procurement — unpaid supply of goods
    completeness=4/5  factual_ground=4/5  actionability=5/5
    composite=4.33/5
    comment: Strong citation of Public Procurement Act with clear demand for payment.

  [employment-001] Unfair termination — summary dismissal without notice
    completeness=3/5  factual_ground=5/5  actionability=4/5
    composite=4.00/5
    comment: Employment Act citation is accurate; could address compensation quantum more specifically.

Summary: 11/11 cases completed
Mean composite score: 4.22/5.0  (threshold: 3.0/5.0)
```

**Cost:** ~**$0.30+** per full run (**11** pipeline passes + **11** judge calls on **gpt-4o** — use sparingly; wired only to **manual** dispatch in **`evals.yml`**).

**Exit code:** Returns 0 if mean ≥ threshold, 1 if below.

**Why "LLM-as-judge"?** Having the same model that generated the brief also evaluate it would be biased (the model tends to score its own outputs highly). Using a **second, independent model call** with a different system prompt — framing it as an evaluator, not a creator — gives a more objective score. This is a standard technique in LLM evaluation (popularised by the LMSYS Chatbot Arena research).

---

#### How Evals Differ from Tests

| | Tests (`pytest`) | Evals (`uv run python -m evals.*`) |
|---|---|---|
| AI calls | None (all mocked) | Real OpenAI API calls |
| Cost | Free | ~$0.01–$0.50 per run |
| Speed | ~3 seconds | ~30–120 seconds |
| What they check | Code correctness (schema shapes, HTTP status codes, routing logic) | Output quality (are the facts accurate? is the brief useful?) |
| When to run | On every code change | Before a major release or after changing prompts |
| CI use | Yes — **`backend-deploy.yml`** on push | **`evals.yml`**: extraction eval on filtered **`main`** pushes (**non-blocking** today); judge **manual** only |

---

**Rubric mapping for Evaluation Strategy:**

| What exists | Evidence | Rubric score contribution |
|-------------|----------|--------------------------|
| Golden test cases defined | `golden_cases.json` with **11** labelled cases | Defined metrics and test scenarios (score 3) |
| Automated extraction checks | `eval_extraction.py` validates structured output against constraints | Functional correctness checked (score 3-4) |
| LLM-as-judge scoring | `eval_llm_judge.py` scores completeness, factual grounding, actionability | LLM output quality assessed (score 4) |
| Configurable pass threshold | `--threshold` on **`eval_llm_judge`** (default **3.0** in **`evals.yml`**) | Measurable quality baseline (score 4) |
| Automated eval visibility | **`evals.yml`** runs extraction eval in GitHub Actions when agent/eval/corpus paths change | Shows eval discipline in CI (rubric “evaluation strategy” narrative) |

**What is missing for score 5:**
- **Hard** CI gate on golden extraction (requires **`OPENAI_API_KEY`** + removing **`continue-on-error`** on **`extraction-eval`**)
- Human review layer (a lawyer reviewing a sample of outputs monthly)
- Regression test tracking (storing scores over time to detect prompt degradation)
- More golden cases (3 is a start; 20+ would give statistical confidence)
- The QA agent itself is a lightweight automated judge — but not a separate evaluation framework

---

## 23. Improvements and Further Steps

The improvements below are split into two categories. Read the tags carefully:

> `[RUBRIC-CRITICAL]` — These directly and significantly affect your capstone score. Do these first, in this order.
>
> `[QUALITY]` — These make the product better in a real-world sense but do not move the rubric needle as much. Do these after the rubric-critical items.

Each improvement includes: what to do, why it matters for the rubric, and roughly how much effort it takes.

---

### Priority 1 — Rubric-Critical Improvements

---

#### `[RUBRIC-CRITICAL]` 1. Harden CI where it is still soft
**Rubric impact:** Engineering Practices (tests) is already strong via **`backend-deploy.yml`**. Production Readiness (**evaluation strategy**) moves from “scripts exist” to “**merge‑blocking** golden eval” if you want a stricter story.

**Current state:** **`.github/workflows/backend-deploy.yml`** already runs **ruff**, **mypy**, **pytest**, and a **coverage floor**. **`.github/workflows/evals.yml`** runs **`eval_extraction`** on relevant **`main`** pushes but with **`continue-on-error: true`**, so eval failures do not block merges (and runs without **`OPENAI_API_KEY`** fail the step while the workflow stays green).

**What to do (optional):**
1. Add **`OPENAI_API_KEY`** as a GitHub Actions **secret** for this repository.
2. Remove **`continue-on-error: true`** from the **`extraction-eval`** job when you are ready for golden-case regressions to **fail the workflow** and block merges.

**Effort:** ~15 minutes plus secret management policy. Keep **`llm-judge`** on **manual** dispatch to control cost.

---

#### `[RUBRIC-CRITICAL]` 2. Expand golden evaluation coverage (optional)
**Rubric impact:** Production Readiness: Evaluation Strategy → stronger evidence if you push well beyond the current corpus.

**Current state:** **`golden_cases.json`** already ships **11** labelled scenarios (land, procurement, employment, arbitration, tort, limitation, succession, marriage, CPA, constitutional, civil procedure — see the file for IDs).

**What to do:** Add more domains or harder edge cases (e.g. multi-party disputes, conflicting dates, cross-border elements) using the same JSON shape documented in **`docs/rag_enrichments_evals_guide.md`**. Re-run **`eval_extraction`** (and occasionally **`eval_llm_judge`**) after substantive prompt changes.

**Effort:** 2–3 hours per batch of high-quality synthetic matters.

---

#### `[RUBRIC-CRITICAL]` 3. Add a token-cost and latency dashboard in the README/docs
**Rubric impact:** Production Readiness: Solution Feasibility → demonstrates "cost, scaling, and edge cases considered" for score 4

**Current state:** The logs contain `prompt_tokens` and `completion_tokens` per step but there is no summary of what a case costs.

**What to do:** Run the LLM judge eval once, capture the token counts, and add a cost table to the README:

```markdown
## Cost per Case (approximate)

| Step | Model | Avg prompt tokens | Avg completion tokens | Avg cost |
|------|-------|------------------|-----------------------|----------|
| Extraction | gpt-4o-mini | ~600 | ~350 | ~$0.001 |
| Strategy | gpt-4o | ~1200 | ~600 | ~$0.015 |
| Drafting | gpt-4o | ~1800 | ~1200 | ~$0.030 |
| QA | gpt-4o-mini | ~2000 | ~400 | ~$0.002 |
| **Total per case** | | | | **~$0.05** |
```

**Effort:** 30 minutes. Run the eval, read the token logs, write the table.

---

#### `[RUBRIC-CRITICAL]` 4. Add a brief observability section to the README with example log output
**Rubric impact:** Engineering Practices: Observability → jumps from 3→4 ("Strong observability with metrics, tracing, and dashboards")

**Current state:** Structlog is fully wired up and every LLM call is logged with tokens and duration, but this is not documented anywhere visible to an evaluator.

**What to do:** Add a section to the README showing:
1. A sample of the production JSON log output
2. Suggested `jq` queries an operator could run: `cat app.log | jq 'select(.event == "llm_call_complete") | .duration_ms'`
3. A note about which log aggregator you would use in production (e.g., "In production, ship logs to Datadog/Papertrail with `LOG_LEVEL=INFO APP_ENV=production`")

**Effort:** 1–2 hours.

---

#### `[RUBRIC-CRITICAL]` 5. Deploy to a live URL (even a free tier)
**Rubric impact:** Production Readiness: Deployment → jumps from 2→3 ("Functional deployment to a live environment")

**Current state:** Dockerfile exists, docker-compose exists, but there is no live deployment.

**What to do:** The infrastructure is already defined in Terraform. Deploy using GCP Cloud Run for both frontend and backend, with Cloud SQL (PostgreSQL) as the production database:

**Database (GCP Cloud SQL for PostgreSQL):**
1. `cd terraform/database && terraform init && terraform apply`
2. Note the Cloud SQL public IP and Secret Manager ids from Terraform outputs (`cloudsql_public_ip`, `database_url_secret_id`)

**Backend (GCP Cloud Run):**
1. Build and push the Docker image: `docker build -t litigation-backend ./backend && docker push <artifact-registry-image-url>`
2. `cd terraform/backend && terraform init && terraform apply`
3. Secrets are managed by Terraform in GCP Secret Manager (backend env vars + `DATABASE_URL`)

**Frontend (GCP Cloud Run):**
1. Build and push the Docker image: `docker build -t litigation-frontend ./frontend && docker push <artifact-registry-image-url>`
2. `cd terraform/frontend && terraform init && terraform apply`
3. Pass `NEXT_PUBLIC_API_URL` (backend Cloud Run URL) as a Terraform build arg variable

**Effort:** 2–4 hours (mostly GCP project/IAM setup, Artifact Registry pushes, and Terraform apply).

---

#### `[RUBRIC-CRITICAL]` 6. Document the architecture decision record (ADR) for multi-agent vs. single prompt
**Rubric impact:** Technical Depth: Architecture & Design Choices → moves solidly to 4–5 ("deliberate trade-offs documented and defensible")

**Current state:** Design decisions are explained in this walkthrough document, but not in the main README where evaluators will look first.

**What to do:** Add a "Design Decisions" section to `README.md` with a table:

```markdown
## Key Design Decisions

| Decision | Chosen approach | Main alternative | Why we chose this |
|----------|----------------|-----------------|-------------------|
| Agent count | 5 sequential agents | 1 monolithic prompt | Each step validated with Pydantic; cheaper model for simpler steps |
| Structured output | instructor + Pydantic | Prompt-only JSON | Automatic retry on malformed output; schema as documentation |
| Streaming | SSE | Long-poll / single response | Results visible as each step completes; simpler than WebSockets |
| ... | | | |
```

**Effort:** 30–60 minutes.

---

### Priority 2 — Quality Improvements

---

#### `[QUALITY]` 7. Add a per-request correlation ID to logs
**Why:** Currently you can find all log lines for a pipeline run using `case_id`, but the HTTP access log (from the middleware) does not include `case_id` — only path and status. Adding a `request_id` that flows from the middleware into the pipeline logs would let you trace a single request end-to-end through all log lines.

**How:** In `main.py`'s request logger middleware, generate a UUID and store it in structlog's `contextvars`:
```python
import uuid
from structlog.contextvars import bind_contextvars, clear_contextvars

# At the start of each request:
clear_contextvars()
bind_contextvars(request_id=str(uuid.uuid4()))
```
Every subsequent log line in that request (including from agents) will automatically include `request_id`.

**Effort:** 1–2 hours.

---

#### `[QUALITY]` 8. Validate file upload file size limit
**Why:** Currently a user could upload a 100MB PDF. The backend would read it all into memory, potentially crashing the server or causing an out-of-memory error.

**How:** In `services/case_file_text.py`:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

content = await upload.read()
if len(content) > MAX_FILE_SIZE:
    raise HTTPException(413, "File too large. Maximum size is 10 MB.")
```

**Effort:** 30 minutes.

---

#### `[QUALITY]` 9. Add rate limiting per user
**Why:** A single user could hammer the `/analyze` endpoint, running up your OpenAI bill or starving other users.

**How:** Use `slowapi` (a FastAPI-compatible rate limiting library):
```bash
uv add slowapi
```
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze")
@limiter.limit("5/minute")
async def analyze(request: Request, ...):
    ...
```

**Effort:** 2–3 hours.

---

#### `[QUALITY]` 10. Add type hints to all frontend API functions
**Why:** `lib/api.ts` exports functions like `postAnalyzeStream` with correct TypeScript types, but the return types and error shapes could be made stricter using TypeScript's `Result<T, E>` pattern or discriminated unions.

**How:** The existing code is already typed reasonably well. The improvement would be using `zod` to validate API responses at runtime:
```typescript
import { z } from "zod";

const HistoryItemSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  raw_input: z.string(),
  status: z.enum(["PROCESSING", "COMPLETED", "FAILED"]),
  created_at: z.string().datetime(),
});

// In getCases():
const raw = await response.json();
return HistoryItemSchema.array().parse(raw); // throws if API contract broken
```

**Effort:** 3–4 hours.

---

#### `[QUALITY]` 11. Add a "copy brief to clipboard" button
**Why:** The primary output of this tool is the drafted brief. Users will want to copy it into a Word document or email. Currently they have to manually select all text.

**How:** In `pipeline-markdown-panel.tsx`:
```tsx
<button onClick={() => navigator.clipboard.writeText(section.markdown)}>
  Copy
</button>
```

**Effort:** 1 hour.

---

#### `[QUALITY]` 12. Add a "download brief as PDF" feature
**Why:** Lawyers work with PDF documents, not Markdown. Being able to download the final brief as a formatted PDF would be a major usability improvement.

**How:** Use `react-pdf` or simply use the browser's print-to-PDF functionality:
```typescript
// Simplest approach: print just the brief section
window.print();
```
More polished: a backend endpoint that takes the brief Markdown, converts it to HTML with a Kenyan-legal-style CSS stylesheet, and returns a PDF via `weasyprint`.

**Effort:** 4–8 hours.

---

#### `[QUALITY]` 13. Add per-step timing display to the UI
**Why:** Users watching the pipeline stream don't know how long each step took. Showing "Extracted in 2.1s / Strategy in 8.3s" adds transparency and sets expectations.

**How:** Record `Date.now()` when each SSE section arrives and display it next to the section heading in `pipeline-markdown-panel.tsx`.

**Effort:** 2 hours.

---

#### `[QUALITY]` 14. Add a "re-run failed step" button
**Why:** If the strategy agent fails (e.g., OpenAI rate limit), the entire case is marked FAILED. The user has to re-submit the whole form. A "retry" button that resumes from the failed step would be much better UX.

**How:** This requires a new API endpoint (e.g., `POST /api/v1/cases/{id}/retry`) that re-runs the pipeline from the last failed step. The orchestrator would need to read the existing completed steps from the database rather than starting fresh.

**Effort:** 1–2 days (non-trivial — requires orchestrator changes to support resumption).

---

#### `[QUALITY]` 15. Add sentence-level source attribution to the brief
**Why:** A significant hallucination risk in legal AI is the model adding facts not in the original case notes. The QA agent flags this, but it does not tell you *which sentences* are unsupported.

**How:** After drafting, run a second structured prompt that maps each sentence in the brief to a source fact from the extraction result. Sentences with no source mapping are flagged inline. This would significantly improve the `factual_ground` eval score.

**Effort:** 1–2 days.

---

#### `[QUALITY]` 16. Expand the RAG corpus with more Kenyan legal documents
**Why:** The current RAG system is only as good as the legal documents in `data/raw/`. A richer corpus means more relevant precedents retrieved, which directly improves strategy quality.

**What to add to `data/raw/`:**
- Contract Act (Cap 23) — full text
- Land Registration Act (No. 3 of 2012) — full text
- Employment Act (2007) — full text
- Civil Procedure Act (Cap 21) — key sections
- Evidence Act (Cap 80) — key sections
- Selected Court of Appeal judgments on land disputes and contract law

All Kenyan Acts are publicly available on kenyalaw.org.

**Effort:** 2–4 hours (downloading + re-running `uv run python -m src.rag.ingestion`).

---

#### `[QUALITY]` 17. Add a "case template" picker on the new-scan page
**Why:** Many cases fall into recognisable categories (land dispute, employment, supply contract). Pre-filling the form with a template reduces the user's effort and produces more consistent input to the pipeline.

**How:** A dropdown with options: "Land Dispute", "Employment Dispute", "Contract Breach", "Government Procurement". Selecting one fills in a prompt template with placeholders like "[CLAIMANT NAME]".

**Effort:** 3–4 hours (frontend only).

---

#### `[QUALITY]` 18. Set up LLM-based regression testing
**Why:** When you change a prompt (e.g., improve the drafting agent's instructions), you want to know whether the change made outputs better or worse. Without automated comparison, you have no way to know.

**How:** Run the LLM judge eval before and after a prompt change:
```bash
# Before change:
uv run python -m evals.eval_llm_judge > before.txt

# Make your prompt change...

# After change:
uv run python -m evals.eval_llm_judge > after.txt

# Compare:
diff before.txt after.txt
```
Store the baseline scores in `evals/baseline_scores.json` and fail the eval if any score regresses.

**Effort:** 2–3 hours to add baseline comparison logic to `eval_llm_judge.py`.

---

### Summary — What to Do First

If you have **one day** before the demo:
1. `[RUBRIC-CRITICAL]` 1 — Harden eval CI gate: secret + drop `continue-on-error` (~15 min, optional)
2. `[RUBRIC-CRITICAL]` 3 — Add cost table to README (30 min)
3. `[RUBRIC-CRITICAL]` 6 — Add design decisions table to README (30 min)
4. `[RUBRIC-CRITICAL]` 4 — Add observability section to README (1 hour)

If you have **two to three days**:
5. `[RUBRIC-CRITICAL]` 2 — Add 5 more golden cases (2–3 hours)
6. `[RUBRIC-CRITICAL]` 5 — Deploy to GCP Cloud Run + Cloud SQL (2–4 hours)
7. `[QUALITY]` 11 — Copy brief button (1 hour)
8. `[QUALITY]` 16 — Expand RAG corpus (2–3 hours)

If you have **a week**:
9. `[QUALITY]` 7 — Correlation IDs in logs
10. `[QUALITY]` 13 — Per-step timing display
11. `[QUALITY]` 9 — Rate limiting
12. `[QUALITY]` 18 — Regression testing

---

*This document was last updated April 2026 based on a comprehensive code review of the agent-juris repository.*
