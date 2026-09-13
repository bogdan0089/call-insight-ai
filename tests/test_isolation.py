import httpx
import pytest

from app.models.users import User, UserRole
from tests.conftest import auth_header, make_org_user

AUDIO = {"file": ("call.mp3", b"\xff\xfb\x90fake", "audio/mpeg")}


async def upload(client: httpx.AsyncClient, user: User) -> int:
    response = await client.post("/calls", files=AUDIO, headers=auth_header(user))
    assert response.status_code == 202
    return response.json()["id"]


@pytest.mark.asyncio
async def test_a_call_is_invisible_to_another_company(
    client: httpx.AsyncClient,
) -> None:
    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)
    call_id = await upload(client, ours)

    mine = await client.get(f"/calls/{call_id}/report", headers=auth_header(ours))
    alien = await client.get(f"/calls/{call_id}/report", headers=auth_header(theirs))

    assert mine.status_code == 200
    assert alien.status_code == 404


@pytest.mark.asyncio
async def test_listing_never_leaks_across_companies(
    client: httpx.AsyncClient,
) -> None:
    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)
    await upload(client, ours)

    listing = await client.get("/calls", headers=auth_header(theirs))

    assert listing.status_code == 200
    assert listing.json()["total"] == 0


@pytest.mark.asyncio
async def test_operator_sees_only_own_calls(client: httpx.AsyncClient) -> None:
    owner = await make_org_user(UserRole.OWNER)
    operator = await make_org_user(
        UserRole.OPERATOR, organization_id=owner.organization_id
    )

    own_id = await upload(client, operator)
    foreign_id = await upload(client, owner)

    own = await client.get(f"/calls/{own_id}/report", headers=auth_header(operator))
    foreign = await client.get(
        f"/calls/{foreign_id}/report", headers=auth_header(operator)
    )

    assert own.status_code == 200
    assert foreign.status_code == 404


@pytest.mark.asyncio
async def test_operator_cannot_upload_for_someone_else(
    client: httpx.AsyncClient,
) -> None:
    operator = await make_org_user(UserRole.OPERATOR)
    other = await make_org_user(UserRole.OPERATOR)

    response = await client.post(
        "/calls",
        files=AUDIO,
        data={"operator_id": str(other.id)},
        headers=auth_header(operator),
    )

    assert response.status_code == 202
    assert response.json()["operator_id"] == operator.id


@pytest.mark.asyncio
async def test_operator_cannot_verify_scores(client: httpx.AsyncClient) -> None:
    operator = await make_org_user(UserRole.OPERATOR)
    call_id = await upload(client, operator)

    response = await client.patch(
        f"/calls/{call_id}/scores/1",
        json={"is_verified": True},
        headers=auth_header(operator),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    ["/calls", "/calls/1", "/calls/1/report", "/stats/operators", "/stats/checklist"],
)
async def test_every_read_endpoint_requires_a_token(
    client: httpx.AsyncClient,
    path: str,
) -> None:
    assert (await client.get(path)).status_code == 401


@pytest.mark.asyncio
async def test_statistics_only_counts_own_company(client: httpx.AsyncClient) -> None:
    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)
    await upload(client, ours)

    stats = await client.get("/stats/operators", headers=auth_header(theirs))

    assert stats.status_code == 200
    assert stats.json() == []


@pytest.mark.asyncio
async def test_checklist_statistics_only_count_own_company(
    client: httpx.AsyncClient,
) -> None:
    from app.core.db import async_session
    from app.models.calls import Call, CallStatus
    from app.models.checklist import ChecklistItem
    from app.models.scores import CallScore

    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)

    async with async_session() as session:
        item = ChecklistItem(
            organization_id=ours.organization_id,
            code="leak_probe",
            title="probe",
            description="probe",
        )
        call = Call(
            audio_path="probe.mp3",
            organization_id=ours.organization_id,
            operator_id=ours.id,
            status=CallStatus.DONE,
        )
        session.add_all([item, call])
        await session.flush()
        session.add(CallScore(call_id=call.id, checklist_item_id=item.id, passed=True))
        await session.commit()
        item_id = item.id

    stats = await client.get("/stats/checklist", headers=auth_header(theirs))

    assert stats.status_code == 200
    assert item_id not in [row["checklist_item_id"] for row in stats.json()]

