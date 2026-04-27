"""
Tests for GET /api/v1/cases and GET /api/v1/cases/{id}.

Key production-readiness checks:
- User isolation: users cannot see each other's cases (critical for multi-tenant)
- Ordering: most recent case appears first
- DB persistence: all 5 agent step results are stored and retrievable
- 404 semantics: nonexistent IDs and cross-user access both return 404
"""

import asyncio
from datetime import datetime

from tests.conftest import (
    ANALYZE_FORM_BODY,
    HEADERS_A,
    HEADERS_B,
    SAMPLE_CASE,
    collect_sse,
    run_analyze,
)

EXPECTED_STEP_NAMES = ["extraction", "rag_retrieval", "strategy", "drafting", "qa"]


# ── Empty state ───────────────────────────────────────────────────────────────


async def test_history_empty_for_brand_new_user(client):
    r = await client.get("/api/v1/cases", headers=HEADERS_A)
    assert r.status_code == 200
    assert r.json() == []


async def test_history_empty_for_user_with_no_cases(client, mock_agents):
    """User B gets empty list even when User A has cases."""
    await run_analyze(client, headers=HEADERS_A)
    r = await client.get("/api/v1/cases", headers=HEADERS_B)
    assert r.status_code == 200
    assert r.json() == []


# ── After a successful analysis ───────────────────────────────────────────────


async def test_history_has_one_entry_after_analyze(client, mock_agents):
    await run_analyze(client)
    history = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert len(history) == 1


async def test_history_entry_status_is_completed(client, mock_agents):
    await run_analyze(client)
    history = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert history[0]["status"] == "COMPLETED"


async def test_history_entry_has_required_fields(client, mock_agents):
    await run_analyze(client)
    item = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()[0]
    for field in ["id", "title", "raw_input", "status", "created_at"]:
        assert field in item, f"Missing field: {field}"


async def test_history_entry_raw_input_matches_submitted_text(client, mock_agents):
    await run_analyze(client)
    item = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()[0]
    assert item["raw_input"] == SAMPLE_CASE.strip()


async def test_history_accumulates_multiple_cases(client, mock_agents):
    await run_analyze(client)
    await run_analyze(client)
    history = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert len(history) == 2


# ── Ordering ──────────────────────────────────────────────────────────────────


async def test_history_most_recent_case_first(client, mock_agents):
    await run_analyze(client)
    await asyncio.sleep(0.05)
    await run_analyze(client)
    history = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert len(history) == 2
    t0 = datetime.fromisoformat(history[0]["created_at"])
    t1 = datetime.fromisoformat(history[1]["created_at"])
    assert t0 >= t1


# ── User isolation (critical) ─────────────────────────────────────────────────


async def test_user_a_cannot_see_user_b_cases(client, mock_agents):
    await run_analyze(client, headers=HEADERS_B)
    history_a = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert history_a == []


async def test_each_user_sees_only_their_own_cases(client, mock_agents):
    await run_analyze(client, headers=HEADERS_A)
    await run_analyze(client, headers=HEADERS_B)
    assert len((await client.get("/api/v1/cases", headers=HEADERS_A)).json()) == 1
    assert len((await client.get("/api/v1/cases", headers=HEADERS_B)).json()) == 1


async def test_user_isolation_by_case_id(client, mock_agents):
    """User B must get 404 when requesting User A's case ID directly."""
    case_id = await run_analyze(client, headers=HEADERS_A)
    r = await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_B)
    assert r.status_code == 404


# ── Detail endpoint ───────────────────────────────────────────────────────────


async def test_case_detail_returns_200(client, mock_agents):
    case_id = await run_analyze(client)
    r = await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)
    assert r.status_code == 200


async def test_case_detail_includes_title(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    assert detail["title"] == ANALYZE_FORM_BODY["title"]


async def test_list_cases_search_by_title_substring(client, mock_agents):
    await run_analyze(client)
    sub = ANALYZE_FORM_BODY["title"].split()[0]
    r = await client.get("/api/v1/cases", params={"q": sub}, headers=HEADERS_A)
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_list_cases_title_search_no_match_returns_empty(client, mock_agents):
    await run_analyze(client)
    r = await client.get("/api/v1/cases", params={"q": "ZZZZnonexistent"}, headers=HEADERS_A)
    assert r.json() == []


async def test_delete_case_returns_204_and_removes(client, mock_agents):
    case_id = await run_analyze(client)
    r = await client.delete(f"/api/v1/cases/{case_id}", headers=HEADERS_A)
    assert r.status_code == 204
    assert (await client.get("/api/v1/cases", headers=HEADERS_A)).json() == []


async def test_delete_case_cross_user_returns_404(client, mock_agents):
    case_id = await run_analyze(client, headers=HEADERS_A)
    r = await client.delete(f"/api/v1/cases/{case_id}", headers=HEADERS_B)
    assert r.status_code == 404
    assert len((await client.get("/api/v1/cases", headers=HEADERS_A)).json()) == 1


async def test_case_detail_nonexistent_id_returns_404(client):
    r = await client.get("/api/v1/cases/does-not-exist", headers=HEADERS_A)
    assert r.status_code == 404


async def test_case_detail_has_5_agent_steps(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    assert len(detail["steps"]) == 5


async def test_case_detail_step_names_are_correct(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    names = [s["step_name"] for s in detail["steps"]]
    assert names == EXPECTED_STEP_NAMES


async def test_case_detail_steps_ordered_by_index(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    indices = [s["step_index"] for s in detail["steps"]]
    assert indices == [0, 1, 2, 3, 4]


async def test_case_detail_all_steps_are_completed(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    assert all(s["status"] == "COMPLETED" for s in detail["steps"])


async def test_case_detail_all_steps_have_result(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    assert all(s["result"] is not None for s in detail["steps"])


async def test_case_detail_extraction_step_shape(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    ext_step = next(s for s in detail["steps"] if s["step_name"] == "extraction")
    result = ext_step["result"]
    assert "core_facts" in result
    assert "entities" in result
    assert "chronological_timeline" in result


async def test_case_detail_drafting_step_has_brief_markdown(client, mock_agents):
    case_id = await run_analyze(client)
    detail = (await client.get(f"/api/v1/cases/{case_id}", headers=HEADERS_A)).json()
    draft_step = next(s for s in detail["steps"] if s["step_name"] == "drafting")
    assert "brief_markdown" in draft_step["result"]
    assert isinstance(draft_step["result"]["brief_markdown"], str)


# ── Failed case persistence ───────────────────────────────────────────────────


async def test_failed_case_appears_in_history(client, mock_agents):
    mock_agents["extraction"].side_effect = RuntimeError("boom")
    async with client.stream(
        "POST", "/api/v1/analyze", data=ANALYZE_FORM_BODY, headers=HEADERS_A
    ) as resp:
        await collect_sse(resp)
    history = (await client.get("/api/v1/cases", headers=HEADERS_A)).json()
    assert len(history) == 1
    assert history[0]["status"] == "FAILED"
