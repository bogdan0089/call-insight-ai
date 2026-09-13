from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_keys import router as api_keys_router
from app.api.auth import router as auth_router
from app.api.calls import router as calls_router
from app.api.people import router as people_router
from app.api.stats import router as stats_router
from app.core.config import settings
from app.core.db import get_session
from app.core.logging import configure_logging
from app.exceptions import AppException

configure_logging()

app = FastAPI(title="Call Insight")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(calls_router)
app.include_router(people_router)
app.include_router(api_keys_router)
app.include_router(stats_router)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status_code,
        content={"detail": exc.message, "code": type(exc).__name__, "info": exc.info},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable: {exc}",
        ) from exc
    return {"status": "ready"}
