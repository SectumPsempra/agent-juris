"""Lazily construct the Pinecone index handle used by ingestion and retrieval."""

from functools import lru_cache
from typing import Any

from pinecone import Pinecone

from src.core.config import settings


@lru_cache(maxsize=1)
def get_pinecone_index() -> Any:
    """Return a Pinecone ``Index`` for upserts and queries.

    Prefer ``PINECONE_INDEX_HOST`` (from the Pinecone console for serverless indexes).
    If unset, ``PINECONE_INDEX_NAME`` is used and the client resolves the endpoint.
    """
    if not settings.pinecone_api_key.strip():
        raise ValueError("PINECONE_API_KEY is not set")
    host = settings.pinecone_index_host.strip()
    name = settings.pinecone_index_name.strip()
    if not host and not name:
        raise ValueError("Set PINECONE_INDEX_HOST or PINECONE_INDEX_NAME for RAG")
    pc = Pinecone(api_key=settings.pinecone_api_key)
    if host:
        return pc.Index(host=host)
    return pc.Index(name=name)


def pinecone_configured() -> bool:
    """True when minimal Pinecone settings are present (RAG can run)."""
    if not settings.pinecone_api_key.strip():
        return False
    return bool(settings.pinecone_index_host.strip() or settings.pinecone_index_name.strip())
