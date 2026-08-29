from collections.abc import AsyncGenerator

import httpx
import pytest

from app.core.db import engine
from app.main import app
from app.workers import tasks


@pytest.fixture(autouse=True)
async def dispose_engine() -> AsyncGenerator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def no_celery(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    published: list[int] = []
    monkeypatch.setattr(tasks.process_call, "delay", published.append)
    return published


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
