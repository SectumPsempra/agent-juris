output "cloud_run_url" {
  description = "The URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository id (Docker)"
  value       = google_artifact_registry_repository.backend.repository_id
}

output "image_url" {
  description = "Full image URL (tagged :latest)"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.backend.repository_id}/litigation-backend:latest"
}

output "db_credentials_secret_id" {
  description = "Secret Manager secret id holding DATABASE_URL (string)"
  value       = data.google_secret_manager_secret.database_url.secret_id
}