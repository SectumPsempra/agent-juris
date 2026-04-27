"""Ingest Kenyan legal corpus from data/raw/ into Pinecone.

Run once to build the index:
    uv run python -m src.rag.ingestion

Re-run whenever documents are added to data/raw/.
Requires PINECONE_* and OPENAI_API_KEY (see .env.example).
"""

import asyncio
import uuid
from pathlib import Path

from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.core.openai_client import get_async_client
from src.rag.pinecone_store import get_pinecone_index, pinecone_configured
from src.rag.vector_store import EMBED_MODEL, PINECONE_METADATA_TEXT_KEY

logger = get_logger(__name__)

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
_EMBED_BATCH_SIZE = 256
_PINECONE_UPSERT_BATCH = 100


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-based chunks, stripping whitespace from each."""
    if not text.strip():
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += size - overlap
    return chunks


async def _ingest_documents_async(raw_dir: Path = RAW_DIR) -> dict:
    """Async implementation: embed via ``AsyncOpenAI`` and upsert to Pinecone."""
    txt_files = sorted(raw_dir.glob("*.txt")) + sorted(raw_dir.glob("*.md"))

    if not txt_files:
        logger.warning("ingestion_no_files_found", raw_dir=str(raw_dir))
        return {"detail": "no_files_found", "chunks_added": 0}

    logger.info("ingestion_start", raw_dir=str(raw_dir), file_count=len(txt_files))

    all_docs: list[str] = []
    all_ids: list[str] = []
    all_metadata: list[dict[str, str | int]] = []

    for fpath in txt_files:
        text = fpath.read_text(encoding="utf-8", errors="replace")
        file_chunks = chunk_text(text)
        for i, chunk in enumerate(file_chunks):
            all_docs.append(chunk)
            all_ids.append(f"{fpath.stem}_{i}_{uuid.uuid4().hex[:6]}")
            all_metadata.append(
                {
                    PINECONE_METADATA_TEXT_KEY: chunk,
                    "source": fpath.name,
                    "chunk_index": i,
                }
            )
        logger.info("ingestion_file_processed", file=fpath.name, chunks=len(file_chunks))

    if not all_docs:
        logger.warning("ingestion_no_content", raw_dir=str(raw_dir))
        return {"detail": "no_content", "chunks_added": 0}

    if not pinecone_configured():
        raise ValueError(
            "Pinecone is not configured. Set PINECONE_API_KEY and "
            "PINECONE_INDEX_HOST (or PINECONE_INDEX_NAME) in the environment."
        )

    logger.info(
        "ingestion_embed_start",
        total_chunks=len(all_docs),
        batch_size=_EMBED_BATCH_SIZE,
        model=EMBED_MODEL,
    )

    client = get_async_client()
    embeddings: list[list[float]] = []
    for i in range(0, len(all_docs), _EMBED_BATCH_SIZE):
        batch = all_docs[i : i + _EMBED_BATCH_SIZE]
        resp = await client.embeddings.create(model=EMBED_MODEL, input=batch)
        embeddings.extend(item.embedding for item in resp.data)
        logger.info(
            "ingestion_embed_batch_complete",
            batch_start=i,
            batch_end=min(i + _EMBED_BATCH_SIZE, len(all_docs)),
        )

    index = get_pinecone_index()
    ns = settings.pinecone_namespace.strip()

    for start in range(0, len(all_docs), _PINECONE_UPSERT_BATCH):
        end = start + _PINECONE_UPSERT_BATCH
        batch_vectors = [
            {"id": all_ids[j], "values": embeddings[j], "metadata": all_metadata[j]}
            for j in range(start, min(end, len(all_docs)))
        ]
        upsert_kwargs: dict = {"vectors": batch_vectors}
        if ns:
            upsert_kwargs["namespace"] = ns
        index.upsert(**upsert_kwargs)
        logger.info(
            "ingestion_upsert_batch_complete",
            batch_start=start,
            batch_end=min(end, len(all_docs)),
        )

    logger.info("ingestion_complete", chunks_added=len(all_docs))
    return {"detail": "ok", "chunks_added": len(all_docs)}


def ingest_documents(raw_dir: Path = RAW_DIR, persist_dir: str | None = None) -> dict:
    """Load all .txt and .md files from raw_dir, chunk, embed, and upsert to Pinecone.

    ``persist_dir`` is accepted for backward compatibility with tests and callers
    that previously pointed at Chroma on disk; it is ignored.

    Synchronous entry point for scripts and tests; runs the async pipeline with
    ``asyncio.run``.
    """
    _ = persist_dir
    return asyncio.run(_ingest_documents_async(raw_dir=raw_dir))


if __name__ == "__main__":
    configure_logging()
    result = ingest_documents()
    print(result)
