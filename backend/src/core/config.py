from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./litigation.db"
    # Pinecone (RAG). Index must use dimension 1536 and metric cosine for text-embedding-3-small.
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""
    pinecone_index_host: str = ""
    pinecone_namespace: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    model: str = "gpt-4o"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    clerk_jwks_url: str = ""
    allowed_origins: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    # Per-step wall-clock timeout in seconds.  Keeps a hung OpenAI call from
    # stalling the SSE stream indefinitely.
    agent_step_timeout_seconds: int = 120


settings = Settings()
