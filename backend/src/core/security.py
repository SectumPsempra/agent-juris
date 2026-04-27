"""Clerk JWT validation using JWKS.

The JWKS is fetched from Clerk's public endpoint and cached in memory with a
5-minute TTL so the application does not make a network round-trip on every
request while still rotating keys within a reasonable window.
"""

import time
from typing import cast

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from jwt.algorithms import RSAAlgorithm

from src.core.logging import get_logger

logger = get_logger(__name__)

_CACHE_TTL_SECONDS = 300

_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}


async def _fetch_jwks(url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()["keys"]


async def _get_jwks(url: str) -> list[dict]:
    """Return cached JWKS, refreshing when the TTL has elapsed."""
    now = time.monotonic()
    if now - _jwks_cache["fetched_at"] > _CACHE_TTL_SECONDS:
        logger.info("jwks_cache_refresh", url=url)
        _jwks_cache["keys"] = await _fetch_jwks(url)
        _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


async def validate_clerk_jwt(token: str, jwks_url: str) -> dict:
    """Validate a Clerk-issued RS256 JWT and return its payload.

    Raises ``jwt.PyJWTError`` on any validation failure (expired, bad signature,
    unknown key, etc.).  The caller is responsible for mapping this to an HTTP
    401 response.
    """
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    keys = await _get_jwks(jwks_url)
    matching = next((k for k in keys if k.get("kid") == kid), None)
    if matching is None:
        # Force a cache refresh and try once more in case keys rotated.
        _jwks_cache["fetched_at"] = 0.0
        keys = await _get_jwks(jwks_url)
        matching = next((k for k in keys if k.get("kid") == kid), None)

    if matching is None:
        raise jwt.PyJWTError(f"No JWKS key found for kid={kid!r}")

    public_key = cast(RSAPublicKey, RSAAlgorithm.from_jwk(matching))
    payload: dict = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )
    return payload
