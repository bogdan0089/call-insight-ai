import uuid

import httpx
import pytest

AUDIO = {"file": ("call.mp3", b"\xff\xfb\x90fake", "audio/mpeg")}


@pytest.mark.asyncio
async def test_upload_returns_queued_call(
    auth_client: httpx.AsyncClient,
    no_celery: list[int],
) -> None:
    response = await auth_client.post("/calls", files=AUDIO)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["total_score"] is None
    assert no_celery == [body["id"]]


@pytest.mark.asyncio
async def test_upload_is_idempotent_by_external_id(
    auth_client: httpx.AsyncClient,
    no_celery: list[int],
) -> None:
    external_id = uuid.uuid4().hex
    data = {"external_id": external_id}

    first = await auth_client.post("/calls", files=AUDIO, data=data)
    second = await auth_client.post("/calls", files=AUDIO, data=data)

    assert first.json()["id"] == second.json()["id"]
    assert len(no_celery) == 1


@pytest.mark.asyncio
async def test_get_unknown_call_returns_404(auth_client: httpx.AsyncClient) -> None:
    response = await auth_client.get("/calls/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Call not found"


@pytest.mark.asyncio
async def test_uploaded_call_can_be_read_back(auth_client: httpx.AsyncClient) -> None:
    created = await auth_client.post("/calls", files=AUDIO)
    call_id = created.json()["id"]

    response = await auth_client.get(f"/calls/{call_id}")

    assert response.status_code == 200
    assert response.json()["id"] == call_id
