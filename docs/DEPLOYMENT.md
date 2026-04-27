# Infrastructure & Deployment Guide

This guide covers provisioning all GCP infrastructure with Terraform and deploying Docker images for the database, backend, and frontend.

## Architecture

```
GCP Cloud Run (Frontend: Next.js)
        ↓ HTTP
GCP Cloud Run (Backend: FastAPI)
        ↓ asyncpg
GCP Cloud SQL (PostgreSQL)
```

All three modules live under `terraform/` and are managed independently.

## Prerequisites

- `gcloud` installed and authenticated (`gcloud auth login`)
- A GCP project (see `docs/GCP.md` for the project id)
- Terraform >= 1.0 installed
- Docker with buildx support (for `--platform linux/amd64`)
- Permissions in the GCP project to manage: Cloud Run, Artifact Registry, Cloud SQL, Secret Manager, IAM

---

## The Dependency Problem

There is a **circular dependency** between the backend and frontend:

| Service  | Needs at deploy time | Source |
|----------|----------------------|--------|
| Backend  | `allowed_origins` (frontend URL) | Created after frontend deploy |
| Frontend | `NEXT_PUBLIC_API_URL` (backend URL) | Created after backend deploy |

**Resolution strategy:**
1. Deploy backend first with a wildcard `allowed_origins = "*"` placeholder
2. Get the backend URL → deploy frontend
3. Get the frontend URL → update backend `allowed_origins` and re-apply

---

## terraform.tfvars Reference

Fill in these files before running `terraform apply`. Never commit real secrets.

### `terraform/database/terraform.tfvars`

```hcl
gcp_project_id = "agent-juris"
gcp_region     = "europe-west1"

# Optional
db_tier    = "db-f1-micro"
db_version = "POSTGRES_15"
```

### `terraform/backend/terraform.tfvars`

```hcl
gcp_project_id = "agent-juris"
gcp_region     = "europe-west1"

# Set at least one provider key:
# openai_api_key = "sk-proj-<your-openai-key>"
openrouter_api_key = "sk-or-v1-<your-openrouter-key>"

openai_model   = "gpt-4o"
clerk_jwks_url = "https://<your-clerk-instance>.clerk.accounts.dev/.well-known/jwks.json"
clerk_issuer   = "https://<your-clerk-instance>.clerk.accounts.dev"

# Step 1: use wildcard; Step 4: replace with real frontend URL
allowed_origins = "*"
# allowed_origins = "https://<random-id>-<hash>.europe-west1.run.app"
```

### `terraform/frontend/terraform.tfvars`

```hcl
gcp_project_id                    = "agent-juris"
gcp_region                        = "europe-west1"
clerk_secret_key                  = "sk_test_<your-clerk-secret-key>"
next_public_clerk_publishable_key = "pk_test_<your-clerk-publishable-key>"

# Fill in after backend is deployed (Step 2c)
next_public_api_url = "https://<random-id>-<hash>.europe-west1.run.app"
```

---

## Deployment Steps

### Step 1 — Deploy the Database

The database has no dependencies on other services.

```bash
cd terraform/database

terraform init
terraform apply
```

Note the outputs — you'll need the secret ARN when the backend reads DB credentials:

```bash
terraform output database_url_secret_id
terraform output cloudsql_public_ip
```

---

### Step 2 — Deploy the Backend

#### 2a. Create the Artifact Registry repository only

Cloud Run needs an image in Artifact Registry before the service can be created. Provision Artifact Registry first.

```bash
cd terraform/backend

terraform init
terraform apply -target=google_artifact_registry_repository.backend
```

Capture the image URL:

```bash
export BACKEND_IMAGE_URL=$(terraform output -raw image_url)
echo $BACKEND_IMAGE_URL
# e.g. europe-west1-docker.pkg.dev/agent-juris/litigation-backend/litigation-backend:latest
```

#### 2b. Build and push the backend image

```bash
# Authenticate Docker to Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet

# Build for linux/amd64 (recommended for consistency)
cd ../../backend
docker build --platform linux/amd64 -t litigation-backend .

# Tag with the full image URL (required — Docker push needs the registry in the image name)
docker tag litigation-backend:latest $BACKEND_IMAGE_URL

# Push
docker push $BACKEND_IMAGE_URL
```

#### 2c. Deploy the full backend infrastructure

Make sure `terraform/backend/terraform.tfvars` has `allowed_origins = "*"` for now.

```bash
cd ../terraform/backend
terraform apply
```

Capture the backend URL — you need this for the frontend:

```bash
export BACKEND_URL=$(terraform output -raw cloud_run_url)
echo $BACKEND_URL
# e.g. https://litigation-backend-<hash>.europe-west1.run.app
```

---

### Step 3 — Deploy the Frontend

#### 3a. Create the Artifact Registry repository only

```bash
cd ../frontend   # i.e. terraform/frontend

terraform init
terraform apply -target=google_artifact_registry_repository.frontend
```

Capture the image URL:

```bash
export FRONTEND_IMAGE_URL=$(terraform output -raw image_url)
echo $FRONTEND_IMAGE_URL
# e.g. europe-west1-docker.pkg.dev/agent-juris/litigation-frontend/litigation-frontend:latest
```

#### 3b. Build and push the frontend image

`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` are **baked into the image at build time** — they cannot be changed without rebuilding.

```bash
# Set build-time variables — BACKEND_URL already includes https://
export NEXT_PUBLIC_API_URL=$BACKEND_URL
export CLERK_PUBLISHABLE_KEY="pk_test_<your-clerk-publishable-key>"

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet

# Build with build args
cd ../../frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$CLERK_PUBLISHABLE_KEY \
  --platform linux/amd64 \
  -t litigation-frontend .

# Tag with the full image URL
docker tag litigation-frontend:latest $FRONTEND_IMAGE_URL

# Push
docker push $FRONTEND_IMAGE_URL
```

#### 3c. Deploy the full frontend infrastructure

Update `terraform/frontend/terraform.tfvars` with the real backend URL, then apply:

```bash
cd ../terraform/frontend
terraform apply
```

Capture the frontend URL:

```bash
export FRONTEND_URL=$(terraform output -raw cloud_run_url)
echo $FRONTEND_URL
# e.g. https://litigation-frontend-<hash>.europe-west1.run.app
```

---

### Step 4 — Fix Backend CORS

Now that the frontend URL is known, update the backend `allowed_origins` and re-apply.

Edit `terraform/backend/terraform.tfvars` — paste `$FRONTEND_URL` directly, it already includes `https://`:

```hcl
allowed_origins = "https://<random-id>-<hash>.europe-west1.run.app"
```

Apply the change:

```bash
cd terraform/backend
terraform apply
```

This updates the secret in Secret Manager. Cloud Run will use the latest secret version on the next revision (triggered by `terraform apply`).

---

## Re-deploying After Code Changes

Each service has a deploy script that handles Artifact Registry authentication, image build, and push automatically.
Each service has a deploy script that handles Artifact Registry authentication, image build, and push automatically. Cloud Run will use the latest image on the next revision (triggered by `terraform apply`).

### Backend

```bash
./backend/deploy.sh
```

The script resolves `BACKEND_IMAGE_URL` from Terraform state automatically if it is not already exported in your shell.

### Frontend

```bash
./frontend/deploy.sh
```

The script resolves `FRONTEND_IMAGE_URL` and `NEXT_PUBLIC_API_URL` from Terraform state automatically. `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is read from `frontend/.env.local` if not already exported.

> **Note:** The frontend image bakes `NEXT_PUBLIC_*` values at build time. Rebuild whenever `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` changes.

### Manual steps (if needed without the scripts)

**Backend:**

```bash
cd backend
docker build --platform linux/amd64 -t litigation-backend .
docker tag litigation-backend:latest $BACKEND_IMAGE_URL
docker push $BACKEND_IMAGE_URL
```

**Frontend:**

```bash
cd frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$CLERK_PUBLISHABLE_KEY \
  --platform linux/amd64 \
  -t litigation-frontend .
docker tag litigation-frontend:latest $FRONTEND_IMAGE_URL
docker push $FRONTEND_IMAGE_URL
```

If the image URL variables are not set in your shell, recapture them:

```bash
export BACKEND_IMAGE_URL=$(cd terraform/backend && terraform output -raw image_url)
export FRONTEND_IMAGE_URL=$(cd terraform/frontend && terraform output -raw image_url)
```

---

## Teardown / Destroy

Destroy in reverse order to avoid dependency errors. The database should be last.

```bash
# 1. Destroy frontend (no downstream dependencies)
cd terraform/frontend
terraform destroy

# 2. Destroy backend
cd ../backend
terraform destroy

# 3. Destroy database (last — other services depended on it)
cd ../database
terraform destroy
```

> **Note:** Cloud SQL has deletion protection disabled in this config (development-friendly). Enable it before using this in production.
> **Note:** Cloud SQL has deletion protection disabled in this config (development-friendly). Enable it before using this in production.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `terraform init` | Download providers (run once per module) |
| `terraform plan` | Preview changes without applying |
| `terraform apply` | Create/update infrastructure |
| `terraform apply -target=google_artifact_registry_repository.backend` | Create only the Artifact Registry repo |
| `terraform output -raw image_url` | Get Artifact Registry image URL |
| `terraform output -raw cloud_run_url` | Get deployed service URL |
| `terraform destroy` | Tear down all resources in a module |
