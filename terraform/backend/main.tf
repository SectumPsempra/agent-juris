terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

data "google_project" "current" {
  project_id = var.gcp_project_id
}

# --- Enable required APIs ---
resource "google_project_service" "run" {
  project            = var.gcp_project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  project            = var.gcp_project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  project            = var.gcp_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# --- Artifact Registry (Docker) ---
resource "google_artifact_registry_repository" "backend" {
  location      = var.gcp_region
  repository_id = "litigation-backend"
  description   = "Docker repository for backend images"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry]
}

# Ensure Cloud Run service agent can read images from Artifact Registry
resource "google_artifact_registry_repository_iam_member" "backend_reader" {
  location   = google_artifact_registry_repository.backend.location
  repository = google_artifact_registry_repository.backend.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:service-${data.google_project.current.number}@serverless-robot-prod.iam.gserviceaccount.com"
}

locals {
  backend_secret_values = {
    OPENAI_API_KEY      = var.openai_api_key
    OPENROUTER_API_KEY  = var.openrouter_api_key
    MODEL               = var.openai_model
    CLERK_JWKS_URL      = var.clerk_jwks_url
    CLERK_ISSUER        = var.clerk_issuer
    ALLOWED_ORIGINS     = var.allowed_origins
    PINECONE_API_KEY    = var.pinecone_api_key
    PINECONE_INDEX_HOST = var.pinecone_index_host
    PINECONE_INDEX_NAME = var.pinecone_index_name
    PINECONE_NAMESPACE  = var.pinecone_namespace
    LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
    LANGFUSE_SECRET_KEY = var.langfuse_secret_key
    LANGFUSE_HOST       = var.langfuse_host
  }
}

# --- Secret Manager ---
# In GCP, Cloud Run can only map an env var to an entire secret string (no JSON key selection),
# so we store each env var as its own secret.
resource "google_secret_manager_secret" "backend" {
  for_each = local.backend_secret_values

  secret_id = "${var.project_name}-backend-${lower(replace(each.key, "_", "-"))}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "backend" {
  for_each = local.backend_secret_values

  secret      = google_secret_manager_secret.backend[each.key].id
  secret_data = tostring(each.value)
}

# Reference the DATABASE_URL secret created by terraform/database
data "google_secret_manager_secret" "database_url" {
  secret_id = "litigation-database-url"
}

# Service account used by the Cloud Run service at runtime
resource "google_service_account" "backend_runtime" {
  account_id   = "litigation-backend-runtime"
  display_name = "Litigation backend Cloud Run runtime"
}

# Allow runtime SA to access secrets
resource "google_secret_manager_secret_iam_member" "backend_env_secret_accessor" {
  for_each = google_secret_manager_secret.backend

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_db_secret_accessor" {
  secret_id = data.google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_runtime.email}"
}

# --- Cloud Run (backend) ---
resource "google_cloud_run_v2_service" "backend" {
  name     = "litigation-backend"
  location = var.gcp_region

  template {
    service_account = google_service_account.backend_runtime.email

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.backend.repository_id}/litigation-backend:latest"

      ports {
        container_port = 8000
      }

      env {
        name  = "APP_ENV"
        value = "production"
      }

      # Read individual keys from Secret Manager
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["OPENAI_API_KEY"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENROUTER_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["OPENROUTER_API_KEY"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MODEL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["MODEL"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CLERK_JWKS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["CLERK_JWKS_URL"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CLERK_ISSUER"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["CLERK_ISSUER"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ALLOWED_ORIGINS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["ALLOWED_ORIGINS"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["PINECONE_API_KEY"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_INDEX_HOST"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["PINECONE_INDEX_HOST"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_INDEX_NAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["PINECONE_INDEX_NAME"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_NAMESPACE"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["PINECONE_NAMESPACE"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "LANGFUSE_PUBLIC_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["LANGFUSE_PUBLIC_KEY"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "LANGFUSE_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["LANGFUSE_SECRET_KEY"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "LANGFUSE_HOST"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.backend["LANGFUSE_HOST"].secret_id
            version = "latest"
          }
        }
      }

      # DATABASE_URL comes from terraform/database as a string secret
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"

  depends_on = [
    google_artifact_registry_repository.backend,
    google_secret_manager_secret_version.backend,
    google_project_service.run
  ]
}

# Public unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}