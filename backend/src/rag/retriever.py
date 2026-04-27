"""RAG retriever — embed query with OpenAI, then similarity-search Pinecone.

The function signature ``(query: str) -> list[str]`` is the integration contract
with the orchestrator.  Do not change the signature; only this body should need
to change when swapping vector backends.
"""

import asyncio
import time

from src.core.config import settings
from src.core.logging import get_logger
from src.core.openai_client import get_async_client
from src.rag.pinecone_store import get_pinecone_index, pinecone_configured
from src.rag.vector_store import EMBED_MODEL, PINECONE_METADATA_TEXT_KEY

logger = get_logger(__name__)

# Module-level reference shares the process-level AsyncOpenAI singleton.
# Tests that patch "src.rag.retriever._openai" continue to work unchanged
# because patching replaces this name in the module namespace.
_openai = get_async_client()

_DEFAULT_N_RESULTS = 5


def _matches_from_response(resp: object) -> list:
    """Normalize Pinecone query response to a list of match objects."""
    matches = getattr(resp, "matches", None)
    if matches is not None:
        return list(matches)
    if isinstance(resp, dict):
        return list(resp.get("matches") or [])
    return []


async def rag_retrieve(query: str, n_results: int = _DEFAULT_N_RESULTS) -> list[str]:
    """Return the top-k most relevant legal corpus chunks for the given query.

    Returns an empty list if the query is blank, Pinecone is not configured, or
    there are no matches. The blocking Pinecone client runs in a thread pool.
    """
    if not query.strip():
        return []

    if not pinecone_configured():
        logger.warning("rag_pinecone_not_configured", hint="Set PINECONE_* env vars")
        return []

    logger.info("rag_embed_start", model=EMBED_MODEL, query_len=len(query))
    start = time.monotonic()

    embed_resp = await _openai.embeddings.create(model=EMBED_MODEL, input=query)
    query_embedding: list[float] = embed_resp.data[0].embedding

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    logger.info("rag_embed_complete", model=EMBED_MODEL, duration_ms=duration_ms)

    def _query_pinecone() -> list[str]:
        index = get_pinecone_index()
        q_kwargs: dict = {
            "vector": query_embedding,
            "top_k": n_results,
            "include_metadata": True,
        }
        if settings.pinecone_namespace.strip():
            q_kwargs["namespace"] = settings.pinecone_namespace.strip()
        resp = index.query(**q_kwargs)
        docs: list[str] = []
        for m in _matches_from_response(resp):
            meta = getattr(m, "metadata", None) or {}
            if not isinstance(meta, dict):
                meta = dict(meta) if meta else {}
            text = meta.get(PINECONE_METADATA_TEXT_KEY)
            if isinstance(text, str) and text.strip():
                docs.append(text.strip())
        logger.info("rag_retrieve_complete", chunks_returned=len(docs), top_k=n_results)
        return docs

    return await asyncio.to_thread(_query_pinecone)
