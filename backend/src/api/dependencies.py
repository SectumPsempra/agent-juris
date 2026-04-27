"""FastAPI dependency providers for authentication."""

import jwt
from fastapi import Header, HTTPException

from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import validate_clerk_jwt
from src.schemas.api_schemas import CurrentUser

logger = get_logger(__name__)


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> CurrentUser:
    """Resolve the calling user from a Clerk Bearer token.

    In development (``app_env != "production"``) the ``x-user-id`` header is
    accepted as a fallback so local tooling and tests can bypass Clerk without
    needing live tokens.  In production a valid Bearer token is always required.
    """
    if settings.app_env != "production" and authorization is None:
        return CurrentUser(user_id=x_user_id or "dev-user-001")

    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]

    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured on this server",
        )

    try:
        payload = await validate_clerk_jwt(token, settings.clerk_jwks_url)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except jwt.PyJWTError as exc:
        logger.warning("jwt_validation_failed", reason=str(exc))
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user_id: str = payload.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token is missing subject claim")

    return CurrentUser(user_id=user_id)
