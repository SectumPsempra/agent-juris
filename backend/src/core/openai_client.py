"""Singleton factory for the shared AsyncOpenAI client.

Provider resolution order (first match wins):
  1. OPENAI_API_KEY — uses api.openai.com directly.
  2. OPENROUTER_API_KEY — uses openrouter.ai/api/v1 (OpenAI-compatible).
  3. Neither set — raises ``RuntimeError`` at first call.

All agent modules obtain their client through ``get_async_client()`` so that
the underlying connection pool is shared across the process and tests can
override the instance in a single place.
"""

from openai import AsyncOpenAI

from src.core.config import settings

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_client: AsyncOpenAI | None = None


def _langfuse_enabled() -> bool:
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def get_async_client() -> AsyncOpenAI:
    """Return the process-level AsyncOpenAI singleton, creating it on first call.

    Raises ``RuntimeError`` if neither ``OPENAI_API_KEY`` nor
    ``OPENROUTER_API_KEY`` is configured.
    """
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def _build_client() -> AsyncOpenAI:
    client_cls: type[AsyncOpenAI]
    if _langfuse_enabled():
        import os
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
        from langfuse.openai import AsyncOpenAI as _LangfuseAsyncOpenAI
        client_cls = _LangfuseAsyncOpenAI
    else:
        client_cls = AsyncOpenAI

    if settings.openai_api_key:
        return client_cls(api_key=settings.openai_api_key)

    if settings.openrouter_api_key:
        return client_cls(
            api_key=settings.openrouter_api_key,
            base_url=_OPENROUTER_BASE_URL,
        )

    raise RuntimeError(
        "No LLM provider configured. "
        "Set OPENAI_API_KEY (OpenAI) or OPENROUTER_API_KEY (OpenRouter) in your environment."
    )
