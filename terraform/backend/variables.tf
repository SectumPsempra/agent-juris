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
  description = "Project name for tagging and naming"
  type        = string
  default     = "agent-juris"
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "Optional OpenRouter API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_model" {
  description = "OpenAI Model to use"
  type        = string
  default     = "gpt-4o"
}

variable "clerk_jwks_url" {
  description = "Clerk JWKS URL for JWT validation"
  type        = string
}

variable "clerk_issuer" {
  description = "Clerk Issuer URL"
  type        = string
}

variable "allowed_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
}

variable "pinecone_api_key" {
  description = "Pinecone API key for RAG (optional; leave empty to disable vector retrieval)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "pinecone_index_host" {
  description = "Pinecone serverless index host URL from the console (preferred over index name)"
  type        = string
  sensitive   = false
  default     = ""
}

variable "pinecone_index_name" {
  description = "Pinecone index name if host is not used"
  type        = string
  sensitive   = false
  default     = ""
}

variable "pinecone_namespace" {
  description = "Optional Pinecone namespace for isolating vectors in the index"
  type        = string
  sensitive   = false
  default     = ""
}

variable "langfuse_public_key" {
  description = "Langfuse public key for LLM observability (optional; leave empty to disable tracing)"
  type        = string
  sensitive   = false
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for LLM observability"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_host" {
  description = "Langfuse host URL"
  type        = string
  default     = "https://cloud.langfuse.com"
}