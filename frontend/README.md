# Frontend (Next.js)

Next.js **App Router** application for the Litigation Prep Assistant: landing, pricing, auth entry, and dashboard flows for case input, history, and per-case results. This tree is a **scaffold**; Clerk, billing, and API integration are placeholders.

## Requirements

- Node.js **20+** (LTS recommended)
- npm (this project uses `package-lock.json`)

## Install

From this directory (`frontend/`):

```bash
npm install
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server with [Turbopack](https://nextjs.org/docs/app/api-reference/turbopack) (`next dev --turbopack`). |
| `npm run build` | Production build (`next build`). |
| `npm run start` | Serve the production build (`next start`). |
| `npm run lint` | ESLint via Next.js config. |

Default dev URL: `http://localhost:3000`.

**Evals / CI (backend repo):** Golden-case extraction runs in **`.github/workflows/evals.yml`** on path-filtered pushes to **`main`** (**`continue-on-error: true`** until **`OPENAI_API_KEY`** is set and you remove it); the expensive LLM-judge job is **manual** only — see **`../docs/PROJECT_WALKTHROUGH.md`** §22 (this Next.js app is unchanged by those jobs).

## Environment variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend. Defaults to `http://127.0.0.1:8000` in `src/lib/api.ts` when unset. |

Create a local env file if you need overrides (for example `.env.local` — keep secrets out of git). See [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables).

## App Router routes (scaffold)

| Route | Purpose |
|-------|---------|
| `/` | Public landing; signed-in users are sent to `/dashboard`. |
| `/dashboard` | Authenticated home (dashboard overview). |
| `/dashboard/new-scan` | New case scan with streaming `POST /api/v1/analyze`. |
| `/dashboard/scans` | Case list (`GET /api/v1/cases`). |
| `/dashboard/scans/[id]` | Case detail with agent steps. |
| `/subscriptions` | Plans / Clerk `PricingTable` + premium tools. |
| `/public/*` | Marketing-style public routes (e.g. login, pricing redirect). |

`src/proxy.ts` (Clerk middleware) controls auth at the edge; `/dashboard/*` is also gated in `dashboard/layout.tsx`.

## Components (stubs)

Under `src/components/`: domain folders for `forms`, `dashboard`, `agents`, and `ui` provide minimal placeholders for upcoming UI work.

## Deploying on GCP Cloud Run

The frontend is containerised and deployed via GCP Cloud Run. The full infrastructure is managed by Terraform in `terraform/frontend/`.

1. **Build and push** the Docker image (`frontend/Dockerfile`) to the Artifact Registry repository created by Terraform.
2. **Apply Terraform** — `cd terraform/frontend && terraform apply`. Cloud Run serves the container on port 3000.
3. **Environment variables** — `NEXT_PUBLIC_*` values are passed as Docker build args at image build time. `CLERK_SECRET_KEY` is injected at runtime from GCP Secret Manager.

The Cloud Run service URL is available as a Terraform output (`cloud_run_url`).

## TypeScript and paths

`tsconfig.json` maps `@/*` to `src/*` (for example `import { apiBaseUrl } from "@/lib/api"`).
