#!/usr/bin/env bash
set -euo pipefail

REGION="${GCP_REGION:-europe-west1}"
PROJECT_ID="${GCP_PROJECT_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_FRONTEND_DIR="$SCRIPT_DIR/../terraform/frontend"
TERRAFORM_BACKEND_DIR="$SCRIPT_DIR/../terraform/backend"
FRONTEND_DIR="$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Resolve image URL
# ---------------------------------------------------------------------------
if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: GCP_PROJECT_ID is not set."
  echo "  Export it before running: export GCP_PROJECT_ID=your-gcp-project-id"
  exit 1
fi

if [[ -z "${FRONTEND_IMAGE_URL:-}" ]]; then
  echo "FRONTEND_IMAGE_URL not set — fetching from Terraform state..."
  FRONTEND_IMAGE_URL=$(cd "$TERRAFORM_FRONTEND_DIR" && terraform output -raw image_url)
fi
echo "Image: $FRONTEND_IMAGE_URL"

# ---------------------------------------------------------------------------
# Resolve build-time env vars
# ---------------------------------------------------------------------------
if [[ -z "${NEXT_PUBLIC_API_URL:-}" ]]; then
  echo "NEXT_PUBLIC_API_URL not set — fetching backend URL from Terraform state..."
  NEXT_PUBLIC_API_URL=$(cd "$TERRAFORM_BACKEND_DIR" && terraform output -raw cloud_run_url)
fi
echo "API URL: $NEXT_PUBLIC_API_URL"

if [[ -z "${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:-}" ]]; then
  ENV_LOCAL="$FRONTEND_DIR/.env.local"
  if [[ -f "$ENV_LOCAL" ]]; then
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$(grep -E '^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=' "$ENV_LOCAL" | cut -d '=' -f2-)
    echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY read from .env.local"
  fi
fi

if [[ -z "${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:-}" ]]; then
  echo ""
  echo "ERROR: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is not set and was not found in .env.local."
  echo "  Export it before running: export NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_..."
  exit 1
fi

# ---------------------------------------------------------------------------
# Authenticate Docker to Artifact Registry
# ---------------------------------------------------------------------------
echo ""
echo "Authenticating Docker to Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ---------------------------------------------------------------------------
# Build, tag, push
# ---------------------------------------------------------------------------
echo ""
echo "Building frontend image..."
docker build \
  --build-arg NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" \
  --platform linux/amd64 \
  -t litigation-frontend \
  "$FRONTEND_DIR"

echo ""
echo "Tagging and pushing..."
docker tag litigation-frontend:latest "$FRONTEND_IMAGE_URL"
docker push "$FRONTEND_IMAGE_URL"

echo ""
echo "Done. Revisions will be available in Cloud Run after you redeploy (terraform apply or gcloud run deploy)."
