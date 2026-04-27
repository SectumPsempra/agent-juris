"""FastAPI application factory.

Startup sequence:
  1. Logging is configured before any other import that might emit a log line.
  2. The database is initialised via the lifespan handler.
  3. Middleware is registered in outermost-first order (CORS -> request logger).
  4. Routers are mounted under /api/v1.
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import routes_analyze, routes_auth, routes_cases
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.database.session import init_db

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", env=settings.app_env)
    await init_db()
    yield
    logger.info("shutdown")


app = FastAPI(title="Litigation Prep Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        exc_type=type(exc).__name__,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(routes_analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(routes_cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(routes_auth.router, prefix="/api/v1/me", tags=["auth"])


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
