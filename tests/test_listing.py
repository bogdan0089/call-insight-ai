import uuid
from collections.abc import Iterator

import httpx
import pytest
from sqlalchemy import event

from app.core.db import engine

AUDIO = {"file": ("call.mp3", b"\xff\xfb\x90fake", "audio/mpeg")}


@pytest.fixture
def sql_counter() -> Iterator[list[str]]:
    statements: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    yield statements
    event.remove(engine.sync_engine, "before_cursor_execute", record)


@pytest.mark.asyncio
async def test_list_returns_page_envelope(auth_client: httpx.AsyncClient) -> None:
    external_id = uuid.uuid4().hex
    await auth_client.post("/calls", files=AUDIO, data={"external_id": external_id})

    response = await auth_client.get("/calls", params={"limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "limit", "offset", "has_more"}
    assert body["total"] >= 1
    assert len(body["items"]) <= 5


@pytest.mark.asyncio
async def test_list_is_sorted_by_newest_first(auth_client: httpx.AsyncClient) -> None:
    await auth_client.post("/calls", files=AUDIO, data={"external_id": uuid.uuid4().hex})

    items = (await auth_client.get("/calls", params={"limit": 10})).json()["items"]

    created = [item["created_at"] for item in items]
    assert created == sorted(created, reverse=True)


@pytest.mark.asyncio
async def test_list_filters_by_status(auth_client: httpx.AsyncClient) -> None:
    await auth_client.post("/calls", files=AUDIO, data={"external_id": uuid.uuid4().hex})

    items = (await auth_client.get("/calls", params={"status": "queued"})).json()["items"]

    assert items
    assert {item["status"] for item in items} == {"queued"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"score_min": 90, "score_max": 10},
        {"created_from": "2026-09-10", "created_to": "2026-09-01"},
        {"limit": 0},
        {"limit": 500},
        {"status": "bogus"},
    ],
)
async def test_list_rejects_invalid_query(
    auth_client: httpx.AsyncClient,
    params: dict[str, object],
) -> None:
    assert (await auth_client.get("/calls", params=params)).status_code == 422


@pytest.mark.asyncio
async def test_list_query_count_does_not_grow_with_page_size(
    auth_client: httpx.AsyncClient,
    sql_counter: list[str],
) -> None:
    await auth_client.get("/calls", params={"limit": 1})
    small = len(sql_counter)

    sql_counter.clear()
    await auth_client.get("/calls", params={"limit": 100})
    large = len(sql_counter)

    assert small <= 4
    assert large <= 4


@pytest.mark.asyncio
async def test_report_of_unknown_call_returns_404(auth_client: httpx.AsyncClient) -> None:
    assert (await auth_client.get("/calls/999999/report")).status_code == 404


@pytest.mark.asyncio
async def test_report_has_empty_sections_for_fresh_call(
    auth_client: httpx.AsyncClient,
) -> None:
    call_id = (
        await auth_client.post("/calls", files=AUDIO, data={"external_id": uuid.uuid4().hex})
    ).json()["id"]

    body = (await auth_client.get(f"/calls/{call_id}/report")).json()

    assert body["transcript_text"] is None
    assert body["segments"] == []
    assert body["scores"] == []
    assert body["failed_required"] is False
    assert body["verified_count"] == 0


@pytest.mark.asyncio
async def test_verify_rejects_score_from_another_call(
    auth_client: httpx.AsyncClient,
) -> None:
    call_id = (
        await auth_client.post("/calls", files=AUDIO, data={"external_id": uuid.uuid4().hex})
    ).json()["id"]

    response = await auth_client.patch(
        f"/calls/{call_id}/scores/999999",
        json={"is_verified": True},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/stats/operators", "/stats/checklist"])
async def test_stats_run_in_a_single_query(
    auth_client: httpx.AsyncClient,
    sql_counter: list[str],
    path: str,
) -> None:
    response = await auth_client.get(path)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    aggregations = [stmt for stmt in sql_counter if "GROUP BY" in stmt]
    assert len(aggregations) == 1
    assert len(sql_counter) == 2


@pytest.mark.asyncio
async def test_stats_reject_reversed_date_range(auth_client: httpx.AsyncClient) -> None:
    response = await auth_client.get(
        "/stats/operators",
        params={"created_from": "2026-09-10", "created_to": "2026-09-01"},
    )

    assert response.status_code == 422
