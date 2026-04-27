terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

resource "google_project_service_identity" "run" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = "run.googleapis.com"

  depends_on = [google_project_service.run]
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
resource "google_artifact_registry_repository" "frontend" {
  location      = var.gcp_region
  repository_id = "litigation-frontend"
  description   = "Docker repository for frontend images"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry]
}

resource "google_artifact_registry_repository_iam_member" "frontend_reader" {
  location   = google_artifact_registry_repository.frontend.location
  repository = google_artifact_registry_repository.frontend.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_project_service_identity.run.email}"

  depends_on = [google_project_service_identity.run]
}

# --- Secret Manager ---
resource "google_secret_manager_secret" "frontend_secrets" {
  secret_id = "${var.project_name}-frontend-secrets"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "frontend_secrets" {
  secret      = google_secret_manager_secret.frontend_secrets.id
  secret_data = var.clerk_secret_key
}

resource "google_service_account" "frontend_runtime" {
  account_id   = "litigation-frontend-runtime"
  display_name = "Litigation frontend Cloud Run runtime"
}

resource "google_secret_manager_secret_iam_member" "frontend_secret_accessor" {
  secret_id = google_secret_manager_secret.frontend_secrets.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.frontend_runtime.email}"
}

# --- Cloud Run (frontend) ---
resource "google_cloud_run_v2_service" "frontend" {
  name                = "litigation-frontend"
  location            = var.gcp_region
  deletion_protection = false

  template {
    service_account = google_service_account.frontend_runtime.email

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.frontend.repository_id}/litigation-frontend:latest"

      ports {
        container_port = 3000
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }

      env {
        name  = "HOSTNAME"
        value = "0.0.0.0"
      }

      # CLERK_SECRET_KEY is server-side only — safe to inject at runtime.
      # NEXT_PUBLIC_* vars are baked into the image at build time via Docker build args.
      env {
        name = "CLERK_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.frontend_secrets.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"

  depends_on = [
    google_artifact_registry_repository.frontend,
    google_secret_manager_secret_version.frontend_secrets,
    google_project_service.run
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
