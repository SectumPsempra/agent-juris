"""
Tests for the RAG pipeline components.

Three test groups:
  1. chunk_text       — pure unit tests, no mocking needed
  2. rag_retrieve     — mocked OpenAI embeddings + Pinecone index
  3. ingest_documents — mocked OpenAI + temp filesystem + mocked Pinecone

Integration group (bottom of file):
  4. Pipeline integration — RAG chunks flow correctly into the strategy agent
     and are reflected in SSE events and persisted DB results.

All Pinecone and OpenAI calls are mocked; no network, no disk, no API cost.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.rag.ingestion import CHUNK_OVERLAP, CHUNK_SIZE, chunk_text, ingest_documents
from src.rag.retriever import rag_retrieve
from src.rag.vector_store import PINECONE_METADATA_TEXT_KEY
from tests.conftest import ANALYZE_FORM_BODY, HEADERS_A, collect_sse, run_analyze

# ── 1. chunk_text ─────────────────────────────────────────────────────────────


def test_chunk_text_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_chunk_text_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\t  ") == []


def test_chunk_text_short_text_returns_single_chunk():
    assert chunk_text("Short text.", size=CHUNK_SIZE) == ["Short text."]


def test_chunk_text_long_text_produces_multiple_chunks():
    text = "A" * (CHUNK_SIZE + 50)
    result = chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    assert len(result) > 1


def test_chunk_text_no_chunk_exceeds_size():
    text = "word " * 400
    for chunk in chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        assert len(chunk) <= CHUNK_SIZE


def test_chunk_text_all_chunks_non_empty():
    text = "Sample legal text. " * 100
    assert all(c.strip() for c in chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP))


def test_chunk_text_exactly_chunk_size_returns_one_chunk():
    text = "x" * CHUNK_SIZE
    assert len(chunk_text(text, size=CHUNK_SIZE, overlap=0)) == 1


def test_chunk_text_zero_overlap_produces_non_overlapping_chunks():
    text = "x" * 300
    result = chunk_text(text, size=100, overlap=0)
    assert len(result) == 3


def test_chunk_text_overlap_tail_of_first_matches_head_of_second():
    # With overlap=20, the last 20 chars of chunk[0] should equal the first 20 of chunk[1].
    text = "ABCDE" * 200  # 1000 chars
    result = chunk_text(text, size=100, overlap=20)
    assert len(result) >= 2
    assert result[0][-20:] == result[1][:20]


def test_chunk_text_strips_leading_trailing_whitespace_from_each_chunk():
    text = ("  legal content  " * 60).strip()
    for chunk in chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        assert chunk == chunk.strip()


def test_chunk_text_full_coverage_no_content_lost():
    # Every character in the source must appear in at least one chunk (modulo stripping).
    text = "ABCDEFGHIJ" * 200
    chunks = chunk_text(text, size=100, overlap=0)
    # Reassembled with zero overlap should cover the full text length
    total = sum(len(c) for c in chunks)
    assert total == len(text.strip())


# ── 2. rag_retrieve ───────────────────────────────────────────────────────────

# Shared mock factories


def _embed_mock(embedding: list[float] | None = None):
    """AsyncMock for _openai.embeddings.create returning a single embedding."""
    vec = embedding or [0.1] * 1536
    return AsyncMock(return_value=MagicMock(data=[MagicMock(embedding=vec)]))


def _index_mock_for_docs(texts: list[str]):
    """MagicMock Pinecone index whose ``query`` returns matches with metadata."""
    matches = []
    for t in texts:
        m = MagicMock()
        m.metadata = {PINECONE_METADATA_TEXT_KEY: t}
        matches.append(m)
    idx = MagicMock()
    idx.query.return_value = MagicMock(matches=matches)
    return idx


async def test_rag_retrieve_returns_list_of_strings():
    idx = _index_mock_for_docs(["Chunk A.", "Chunk B."])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        result = await rag_retrieve("contract dispute Kenya")
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)


async def test_rag_retrieve_returns_correct_chunk_content():
    expected = ["Section 3(3) Law of Contract Act.", "Section 38 Land Act."]
    idx = _index_mock_for_docs(expected)
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        result = await rag_retrieve("contract dispute")
    assert result == expected


async def test_rag_retrieve_empty_index_returns_empty_list():
    idx = MagicMock()
    idx.query.return_value = MagicMock(matches=[])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        result = await rag_retrieve("anything")
    assert result == []
    idx.query.assert_called_once()


async def test_rag_retrieve_empty_query_returns_empty_list_no_openai_call():
    with patch("src.rag.retriever._openai") as mock_openai:
        result = await rag_retrieve("")
    assert result == []
    mock_openai.embeddings.create.assert_not_called()


async def test_rag_retrieve_whitespace_query_returns_empty_list():
    with patch("src.rag.retriever._openai") as mock_openai:
        result = await rag_retrieve("   \t\n  ")
    assert result == []
    mock_openai.embeddings.create.assert_not_called()


async def test_rag_retrieve_passes_correct_embedding_to_pinecone():
    expected_vec = [0.42] * 1536
    idx = _index_mock_for_docs(["doc"])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock(expected_vec)
        await rag_retrieve("some legal query")
    call_kwargs = idx.query.call_args.kwargs
    assert call_kwargs["vector"] == expected_vec


async def test_rag_retrieve_respects_n_results_argument():
    idx = _index_mock_for_docs(["A", "B"])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        await rag_retrieve("query", n_results=2)
    assert idx.query.call_args.kwargs["top_k"] == 2


async def test_rag_retrieve_passes_requested_top_k_to_pinecone():
    """Pinecone returns up to ``top_k`` matches; we pass the requested value through."""
    idx = _index_mock_for_docs(["A", "B"])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        await rag_retrieve("query", n_results=10)
    assert idx.query.call_args.kwargs["top_k"] == 10


async def test_rag_retrieve_filters_out_empty_document_strings():
    texts = ["Valid chunk.", "", "  ", "Another chunk."]
    matches = []
    for t in texts:
        m = MagicMock()
        m.metadata = {PINECONE_METADATA_TEXT_KEY: t}
        matches.append(m)
    idx = MagicMock()
    idx.query.return_value = MagicMock(matches=matches)
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        result = await rag_retrieve("query")
    assert "" not in result
    assert "  " not in result
    assert len(result) == 2


async def test_rag_retrieve_sets_include_metadata_true():
    idx = _index_mock_for_docs(["doc"])
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=True),
        patch("src.rag.retriever.get_pinecone_index", return_value=idx),
    ):
        mock_openai.embeddings.create = _embed_mock()
        await rag_retrieve("query")
    assert idx.query.call_args.kwargs["include_metadata"] is True


async def test_rag_retrieve_returns_empty_when_pinecone_not_configured():
    with (
        patch("src.rag.retriever._openai") as mock_openai,
        patch("src.rag.retriever.pinecone_configured", return_value=False),
    ):
        result = await rag_retrieve("contract law")
    assert result == []
    mock_openai.embeddings.create.assert_not_called()


# ── 3. ingest_documents ───────────────────────────────────────────────────────


@pytest.fixture
def raw_dir_two_files(tmp_path: Path) -> Path:
    """Temp directory with two representative Kenyan law text files."""
    (tmp_path / "contract_act.txt").write_text(
        "CONTRACT ACT CAP 23\n\n"
        "Section 3(3). A contract for the sale of land must be in writing.\n"
        "Section 10. Specific performance is available where damages are inadequate.\n" * 12,
        encoding="utf-8",
    )
    (tmp_path / "land_act_2012.txt").write_text(
        "LAND ACT NO. 6 OF 2012\n\n"
        "Section 38. Specific performance of agreements for sale of land.\n"
        "Part performance entitles the purchaser to enforce the agreement.\n" * 12,
        encoding="utf-8",
    )
    return tmp_path


def _patch_ingest() -> tuple[MagicMock, MagicMock]:
    """Build mocks for ingest_documents tests (async OpenAI client + Pinecone index)."""
    mock_index = MagicMock()
    mock_client = MagicMock()

    async def _create_embeddings(*args, model=None, input=None, **kwargs):  # noqa: A002
        n = len(input) if isinstance(input, list) else 1
        return MagicMock(data=[MagicMock(embedding=[0.1] * 1536) for _ in range(n)])

    mock_client.embeddings.create = AsyncMock(side_effect=_create_embeddings)
    return mock_index, mock_client


def test_ingest_documents_empty_directory_returns_no_files_found(tmp_path: Path):
    result = ingest_documents(raw_dir=tmp_path, persist_dir=str(tmp_path / "vdb"))
    assert result["detail"] == "no_files_found"
    assert result["chunks_added"] == 0


def test_ingest_documents_raises_when_pinecone_not_configured(
    raw_dir_two_files: Path, tmp_path: Path
):
    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
    )
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=False),
        pytest.raises(ValueError, match="Pinecone is not configured"),
    ):
        ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))


def test_ingest_documents_success_returns_ok_with_chunk_count(
    raw_dir_two_files: Path, tmp_path: Path
):
    mock_index, mock_client = _patch_ingest()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        result = ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    assert result["detail"] == "ok"
    assert result["chunks_added"] > 0


def test_ingest_documents_calls_upsert_at_least_once(raw_dir_two_files: Path, tmp_path: Path):
    mock_index, mock_client = _patch_ingest()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    assert mock_index.upsert.call_count >= 1


def test_ingest_documents_upsert_vectors_match_chunk_count(
    raw_dir_two_files: Path, tmp_path: Path
):
    mock_index, mock_client = _patch_ingest()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        result = ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    total = 0
    for call in mock_index.upsert.call_args_list:
        total += len(call.kwargs["vectors"])
    n = result["chunks_added"]
    assert total == n
    for call in mock_index.upsert.call_args_list:
        for row in call.kwargs["vectors"]:
            assert "id" in row and "values" in row and "metadata" in row
            assert len(row["values"]) == 1536


def test_ingest_documents_chunk_ids_are_all_unique(raw_dir_two_files: Path, tmp_path: Path):
    mock_index, mock_client = _patch_ingest()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    ids: list[str] = []
    for call in mock_index.upsert.call_args_list:
        ids.extend(v["id"] for v in call.kwargs["vectors"])
    assert len(ids) == len(set(ids))


def test_ingest_documents_metadata_records_source_filename(raw_dir_two_files: Path, tmp_path: Path):
    mock_index, mock_client = _patch_ingest()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    sources: set[str] = set()
    for call in mock_index.upsert.call_args_list:
        for row in call.kwargs["vectors"]:
            sources.add(row["metadata"]["source"])
    assert sources == {"contract_act.txt", "land_act_2012.txt"}


def test_ingest_documents_total_embeddings_match_chunks_embedded(
    raw_dir_two_files: Path, tmp_path: Path
):
    """Number of embeddings requested from OpenAI must equal chunks_added."""
    embedded_count: list[int] = []

    async def _create(*args, model=None, input=None, **kwargs):  # noqa: A002
        n = len(input) if isinstance(input, list) else 1
        embedded_count.append(n)
        return MagicMock(data=[MagicMock(embedding=[0.1] * 1536) for _ in range(n)])

    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(side_effect=_create)
    mock_index = MagicMock()
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        result = ingest_documents(raw_dir=raw_dir_two_files, persist_dir=str(tmp_path / "vdb"))
    assert sum(embedded_count) == result["chunks_added"]


def test_ingest_documents_accepts_markdown_files(tmp_path: Path):
    (tmp_path / "notes.md").write_text("## Kenyan Employment Act\nKey provisions.\n" * 15)
    mock_index = MagicMock()
    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
    )
    with (
        patch("src.rag.ingestion.get_async_client", return_value=mock_client),
        patch("src.rag.ingestion.pinecone_configured", return_value=True),
        patch("src.rag.ingestion.get_pinecone_index", return_value=mock_index),
    ):
        result = ingest_documents(raw_dir=tmp_path, persist_dir=str(tmp_path / "vdb"))
    assert result["detail"] == "ok"
    assert result["chunks_added"] > 0


# ── 4. Pipeline integration ───────────────────────────────────────────────────


async def test_strategy_receives_rag_chunks_as_second_argument(client, mock_agents):
    """When rag_retrieve returns chunks, run_strategy_agent must receive them."""
    rag_chunks = [
        "Section 3(3) of the Law of Contract Act requires land sale agreements to be in writing.",
        "Section 38 of the Land Act 2012 allows specific performance for part performance.",
    ]
    mock_agents["rag"].return_value = rag_chunks

    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        await collect_sse(resp)

    call_args = mock_agents["strategy"].call_args
    assert call_args.args[1] == rag_chunks, (
        "Strategy agent second argument must be the RAG chunks returned by rag_retrieve"
    )


async def test_strategy_receives_empty_list_when_rag_returns_nothing(client, mock_agents):
    """Default mock_agents["rag"] returns []; strategy must still receive [] not None."""
    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        await collect_sse(resp)

    call_args = mock_agents["strategy"].call_args
    assert call_args.args[1] == []


async def test_rag_retrieval_sse_section_reflects_non_empty_chunks(client, mock_agents):
    """Non-empty RAG results must appear in the rag_retrieval markdown_section event."""
    mock_agents["rag"].return_value = ["Relevant statute excerpt about land contracts."]

    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        events = await collect_sse(resp)

    rag_event = next(e for e in events if e.get("section_id") == "rag_retrieval")
    assert "Retrieved excerpts" in rag_event["markdown"]
    assert "Relevant statute excerpt" in rag_event["markdown"]


async def test_rag_retrieval_sse_section_shows_no_precedents_when_empty(client, mock_agents):
    """Empty RAG results must produce the 'No precedents' placeholder in SSE."""
    mock_agents["rag"].return_value = []

    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        events = await collect_sse(resp)

    rag_event = next(e for e in events if e.get("section_id") == "rag_retrieval")
    assert "No precedents" in rag_event["markdown"]


async def test_rag_step_stored_in_db_with_correct_chunks(client, mock_agents):
    """rag_retrieval agent_step in DB must record the chunks returned by rag_retrieve."""
    rag_chunks = ["Contract Act Section 3(3).", "Land Act Section 38."]
    mock_agents["rag"].return_value = rag_chunks

    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()

    rag_step = next(s for s in detail["steps"] if s["step_name"] == "rag_retrieval")
    assert rag_step["result"]["chunks"] == rag_chunks


async def test_rag_step_stored_in_db_with_empty_chunks(client, mock_agents):
    """When RAG returns [], the DB step result must record chunks as []."""
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()

    rag_step = next(s for s in detail["steps"] if s["step_name"] == "rag_retrieval")
    assert rag_step["result"]["chunks"] == []


async def test_pipeline_completes_successfully_with_non_empty_rag(client, mock_agents):
    """Full pipeline must reach the complete event even when RAG returns chunks."""
    mock_agents["rag"].return_value = ["Some statute text."]

    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        events = await collect_sse(resp)

    last = events[-1]
    assert last.get("type") == "complete"
    assert "case_id" in last


async def test_rag_step_status_is_completed_in_db(client, mock_agents):
    """The rag_retrieval step in DB must show COMPLETED status after a successful run."""
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()

    rag_step = next(s for s in detail["steps"] if s["step_name"] == "rag_retrieval")
    assert rag_step["status"] == "COMPLETED"


async def test_rag_step_index_is_1(client, mock_agents):
    """rag_retrieval is the second pipeline step (step_index == 1)."""
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()

    rag_step = next(s for s in detail["steps"] if s["step_name"] == "rag_retrieval")
    assert rag_step["step_index"] == 1
