"""
Tests for GET /health.
No auth, no DB, no agents — pure liveness check.
"""


async def test_health_returns_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_health_requires_no_auth(client):
    """Health endpoint must be publicly accessible — no headers at all."""
    r = await client.get("/health")
    assert r.status_code == 200


async def test_health_content_type_is_json(client):
    r = await client.get("/health")
    assert "application/json" in r.headers["content-type"]
