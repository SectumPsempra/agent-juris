"""Shared RAG constants (embedding model, Pinecone metadata schema)."""

EMBED_MODEL = "text-embedding-3-small"
# text-embedding-3-small produces 1536-dimensional vectors (must match Pinecone index).
EMBEDDING_DIMENSION = 1536

# Chunk body is stored in Pinecone vector metadata under this key for query-time retrieval.
PINECONE_METADATA_TEXT_KEY = "text"
