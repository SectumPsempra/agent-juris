"""
Tests for GET /api/v1/me — the stub auth dependency.

John will replace get_current_user with real Clerk JWT validation.
These tests verify the contract that the rest of the app depends on:
  - user_id is always present
  - a missing header falls back to a safe default (won't 500 in dev)
  - any user_id passed in is reflected back unchanged
"""


async def test_me_default_user_when_no_header(client):
    """No x-user-id header → stub returns the dev default."""
    r = await client.get("/api/v1/me")
    assert r.status_code == 200
    assert r.json()["user_id"] == "dev-user-001"


async def test_me_reflects_custom_user_id(client):
    r = await client.get("/api/v1/me", headers={"x-user-id": "alice-test"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "alice-test"


async def test_me_response_has_user_id_key(client):
    body = (await client.get("/api/v1/me")).json()
    assert "user_id" in body


async def test_me_email_is_null_by_default(client):
    """Email is optional — stub returns null until Clerk provides it."""
    body = (await client.get("/api/v1/me")).json()
    assert "email" in body
    assert body["email"] is None


async def test_me_different_users_return_different_ids(client):
    r_alice = await client.get("/api/v1/me", headers={"x-user-id": "alice"})
    r_bob = await client.get("/api/v1/me", headers={"x-user-id": "bob"})
    assert r_alice.json()["user_id"] != r_bob.json()["user_id"]
