terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Using local backend - state will be stored in terraform.tfstate in this directory
  # This is automatically gitignored for security
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Discover project metadata (needed for some IAM bindings)
data "google_project" "current" {
  project_id = var.gcp_project_id
}

# Random password for database
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# --- Enable required APIs (safe to re-apply) ---
resource "google_project_service" "sqladmin" {
  project            = var.gcp_project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  project            = var.gcp_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# ========================================
# Cloud SQL for PostgreSQL (database)
# ========================================

resource "google_sql_database_instance" "postgres" {
  name             = "litigation-postgres"
  database_version = var.db_version
  region           = var.gcp_region

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled = true

      # Development-friendly default. For production, restrict this, or use private IP + VPC connector.
      authorized_networks {
        name  = "public"
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = false

  depends_on = [google_project_service.sqladmin]
}

resource "google_sql_database" "db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# ========================================
# Secret Manager secret for DB credentials
# ========================================

resource "google_secret_manager_secret" "db_credentials" {
  secret_id = "litigation-db-credentials"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_credentials" {
  secret = google_secret_manager_secret.db_credentials.id
  secret_data = jsonencode({
    username = google_sql_user.user.name
    password = random_password.db_password.result
    host     = google_sql_database_instance.postgres.public_ip_address
    port     = 5432
    dbname   = google_sql_database.db.name
    # Connection URL for asyncpg
    db_url = "postgresql+asyncpg://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.postgres.public_ip_address}:5432/${google_sql_database.db.name}"
  })
}

# Convenience secret: DATABASE_URL only (string), for Cloud Run env injection
resource "google_secret_manager_secret" "database_url" {
  secret_id = "litigation-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+asyncpg://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.postgres.public_ip_address}:5432/${google_sql_database.db.name}"
}
