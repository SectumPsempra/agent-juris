variable "gcp_project_id" {
  description = "GCP project id (e.g. agent-juris)"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources (e.g. europe-west1)"
  type        = string
  default     = "europe-west1"
}

variable "db_tier" {
  description = "Cloud SQL machine tier (e.g. db-f1-micro, db-g1-small, db-custom-1-3840)"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "litigation"
}

variable "db_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "litigationadmin"
}

variable "db_version" {
  description = "PostgreSQL version for Cloud SQL"
  type        = string
  default     = "POSTGRES_15"
}