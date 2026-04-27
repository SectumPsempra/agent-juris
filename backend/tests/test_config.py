"""
Unit tests for Settings.parse_allowed_origins and CORS middleware integration.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import Settings

# ── parse_allowed_origins unit tests ─────────────────────────────────────────


def test_comma_string_split_into_list():
    s = Settings(allowed_origins="http://localhost:3000,https://app.example.com")
    assert s.allowed_origins == ["http://localhost:3000", "https://app.example.com"]


def test_single_origin_string_becomes_one_element_list():
    s = Settings(allowed_origins="https://app.example.com")
    assert s.allowed_origins == ["https://app.example.com"]


def test_whitespace_around_origins_is_stripped():
    s = Settings(allowed_origins=" http://a.com , http://b.com ")
    assert s.allowed_origins == ["http://a.com", "http://b.com"]


def test_empty_segments_are_filtered_out():
    s = Settings(allowed_origins="http://a.com,,http://b.com,")
    assert s.allowed_origins == ["http://a.com", "http://b.com"]


def test_list_input_passes_through_unchanged():
    s = Settings(allowed_origins=["http://a.com", "http://b.com"])
    assert s.allowed_origins == ["http://a.com", "http://b.com"]


def test_default_allowed_origins_contains_localhost():
    s = Settings()
    assert "http://localhost:3000" in s.allowed_origins


# ── CORS middleware integration tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_cors_header_returned_for_allowed_origin():
    """CORS preflight for an allowed origin returns the correct allow-origin header."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    origins = ["http://localhost:3000", "https://app.example.com"]
    mini_app = FastAPI()
    mini_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @mini_app.get("/ping")
    def ping():
        return {}

    async with AsyncClient(
        transport=ASGITransport(app=mini_app), base_url="http://test"
    ) as ac:
        r = await ac.options(
            "/ping",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "https://app.example.com"


@pytest.mark.asyncio
async def test_cors_header_absent_for_disallowed_origin():
    """Origins not in the allowlist must not receive the allow-origin header."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    origins = ["http://localhost:3000"]
    mini_app = FastAPI()
    mini_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @mini_app.get("/ping")
    def ping():
        return {}

    async with AsyncClient(
        transport=ASGITransport(app=mini_app), base_url="http://test"
    ) as ac:
        r = await ac.options(
            "/ping",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert r.headers.get("access-control-allow-origin") != "https://evil.example.com"
