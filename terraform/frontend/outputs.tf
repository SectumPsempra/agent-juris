output "cloud_run_url" {
  description = "The URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository id (Docker)"
  value       = google_artifact_registry_repository.frontend.repository_id
}

output "image_url" {
  description = "Full image URL (tagged :latest)"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.frontend.repository_id}/litigation-frontend:latest"
}

output "frontend_secrets_secret_id" {
  description = "Secret Manager secret id holding frontend runtime secrets (json)"
  value       = google_secret_manager_secret.frontend_secrets.secret_id
}
