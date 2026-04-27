variable "gcp_project_id" {
  description = "GCP project id (e.g. agent-juris)"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources (e.g. europe-west1)"
  type        = string
  default     = "europe-west1"
}

variable "project_name" {
  description = "Project name used for tagging and resource naming"
  type        = string
  default     = "agent-juris"
}

variable "clerk_secret_key" {
  description = "Clerk Secret Key for server-side authentication (injected at runtime)"
  type        = string
  sensitive   = true
}

# The two variables below are NOT injected by Terraform at runtime.
# They exist here so CI/CD can read them and pass them as Docker build args:
#   docker build \
#     --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
#     --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY \
#     -t litigation-frontend .
variable "next_public_api_url" {
  description = "Backend API URL baked into the Next.js bundle at image build time"
  type        = string
}

variable "next_public_clerk_publishable_key" {
  description = "Clerk publishable key baked into the Next.js bundle at image build time"
  type        = string
}
