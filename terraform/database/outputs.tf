output "cloudsql_instance_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloudsql_public_ip" {
  description = "Cloud SQL public IP (development-friendly; lock down for production)"
  value       = google_sql_database_instance.postgres.public_ip_address
}

output "db_credentials_secret_id" {
  description = "Secret Manager secret id holding DB credentials (json, includes db_url)"
  value       = google_secret_manager_secret.db_credentials.secret_id
}

output "db_credentials_secret_resource" {
  description = "Secret Manager secret resource name"
  value       = google_secret_manager_secret.db_credentials.id
}

output "database_url_secret_id" {
  description = "Secret Manager secret id holding DATABASE_URL (string)"
  value       = google_secret_manager_secret.database_url.secret_id
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.db.name
}