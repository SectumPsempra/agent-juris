#!/usr/bin/env bash
set -euo pipefail

REGION="${GCP_REGION:-europe-west1}"
PROJECT_ID="${GCP_PROJECT_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_BACKEND_DIR="$SCRIPT_DIR/../terraform/backend"
BACKEND_DIR="$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Resolve image URL
# ---------------------------------------------------------------------------
if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: GCP_PROJECT_ID is not set."
  echo "  Export it before running: export GCP_PROJECT_ID=your-gcp-project-id"
  exit 1
fi

if [[ -z "${BACKEND_IMAGE_URL:-}" ]]; then
  echo "BACKEND_IMAGE_URL not set — fetching from Terraform state..."
  BACKEND_IMAGE_URL=$(cd "$TERRAFORM_BACKEND_DIR" && terraform output -raw image_url)
fi
echo "Image: $BACKEND_IMAGE_URL"

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
echo "Building backend image..."
docker build \
  --platform linux/amd64 \
  -t litigation-backend \
  "$BACKEND_DIR"

echo ""
echo "Tagging and pushing..."
docker tag litigation-backend:latest "$BACKEND_IMAGE_URL"
docker push "$BACKEND_IMAGE_URL"

echo ""
echo "Done. Revisions will be available in Cloud Run after you redeploy (terraform apply or gcloud run deploy)."
