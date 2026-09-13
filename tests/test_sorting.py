from decimal import Decimal

import httpx
import pytest

from app.core.db import async_session
from app.models.calls import Call, CallStatus
from app.models.users import User, UserRole
from tests.conftest import auth_header, make_org_user

SCORES = [Decimal("40.00"), None, Decimal("90.00"), Decimal("65.50")]


async def seed_calls(owner: User) -> None:
    async with async_session() as session:
        session.add_all(
            Call(
                audio_path=f"sort{index}.mp3",
                organization_id=owner.organization_id,
                operator_id=owner.id,
                status=CallStatus.DONE if score is not None else CallStatus.QUEUED,
                total_score=score,
                duration_sec=(index + 1) * 30,
            )
            for index, score in enumerate(SCORES)
        )
        await session.commit()


async def scores(client: httpx.AsyncClient, owner: User, **params: str) -> list:
    response = await client.get("/calls", headers=auth_header(owner), params=params)
    assert response.status_code == 200
    return [item["total_score"] for item in response.json()["items"]]


@pytest.mark.asyncio
async def test_calls_sort_by_score_ascending_with_nulls_last(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    await seed_calls(owner)

    result = await scores(client, owner, sort_by="total_score", order="asc")

    assert result == ["40.00", "65.50", "90.00", None]


@pytest.mark.asyncio
async def test_calls_sort_by_score_descending_keeps_nulls_last(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    await seed_calls(owner)

    result = await scores(client, owner, sort_by="total_score", order="desc")

    assert result == ["90.00", "65.50", "40.00", None]


@pytest.mark.asyncio
async def test_calls_sort_by_duration(client: httpx.AsyncClient, owner: User) -> None:
    await seed_calls(owner)

    response = await client.get(
        "/calls",
        headers=auth_header(owner),
        params={"sort_by": "duration_sec", "order": "desc"},
    )
    durations = [item["duration_sec"] for item in response.json()["items"]]

    assert durations == sorted(durations, reverse=True)


@pytest.mark.asyncio
async def test_pagination_is_stable_when_values_tie(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    async with async_session() as session:
        session.add_all(
            Call(
                audio_path=f"tie{index}.mp3",
                organization_id=owner.organization_id,
                operator_id=owner.id,
                status=CallStatus.DONE,
                total_score=Decimal("50.00"),
            )
            for index in range(6)
        )
        await session.commit()

    params = {"sort_by": "total_score", "order": "asc", "limit": "3"}
    first = await client.get(
        "/calls", headers=auth_header(owner), params={**params, "offset": "0"}
    )
    second = await client.get(
        "/calls", headers=auth_header(owner), params={**params, "offset": "3"}
    )
    first_ids = {item["id"] for item in first.json()["items"]}
    second_ids = {item["id"] for item in second.json()["items"]}

    assert len(first_ids | second_ids) == 6
    assert not first_ids & second_ids


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/calls", {"sort_by": "hashed_password"}),
        ("/calls", {"order": "sideways"}),
        ("/stats/operators", {"sort_by": "id; DROP TABLE users"}),
        ("/stats/checklist", {"sort_by": "description"}),
        ("/people", {"sort_by": "hashed_password"}),
    ],
)
async def test_unknown_sort_fields_are_rejected(
    client: httpx.AsyncClient,
    owner: User,
    path: str,
    params: dict[str, str],
) -> None:
    response = await client.get(path, headers=auth_header(owner), params=params)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_people_sort_by_role_follows_seniority_not_enum_order(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    for role in (UserRole.OPERATOR, UserRole.MANAGER, UserRole.ADMIN):
        await make_org_user(role, organization_id=owner.organization_id)

    response = await client.get(
        "/people",
        headers=auth_header(owner),
        params={"sort_by": "role", "order": "asc"},
    )
    roles = [person["role"] for person in response.json()["items"]]

    assert roles == ["owner", "admin", "manager", "operator"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    [
        "operator_name",
        "calls_total",
        "calls_scored",
        "avg_score",
        "min_score",
        "max_score",
        "failed_required",
        "failed_required_rate",
    ],
)
async def test_every_operator_metric_is_sortable(
    client: httpx.AsyncClient,
    owner: User,
    field: str,
) -> None:
    await seed_calls(owner)

    for order in ("asc", "desc"):
        response = await client.get(
            "/stats/operators",
            headers=auth_header(owner),
            params={"sort_by": field, "order": order},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["code", "title", "weight", "scored", "passed", "pass_rate"]
)
async def test_every_checklist_metric_is_sortable(
    client: httpx.AsyncClient,
    owner: User,
    field: str,
) -> None:
    for order in ("asc", "desc"):
        response = await client.get(
            "/stats/checklist",
            headers=auth_header(owner),
            params={"sort_by": field, "order": order},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_operator_statistics_are_really_ordered(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    averages = {"weak": Decimal("30.00"), "strong": Decimal("95.00"), "mid": Decimal("60.00")}
    ids: dict[str, int] = {}

    for label, score in averages.items():
        operator = await make_org_user(
            UserRole.OPERATOR, organization_id=owner.organization_id
        )
        ids[label] = operator.id
        async with async_session() as session:
            session.add(
                Call(
                    audio_path=f"{label}.mp3",
                    organization_id=owner.organization_id,
                    operator_id=operator.id,
                    status=CallStatus.DONE,
                    total_score=score,
                )
            )
            await session.commit()

    async def order_of(direction: str) -> list[int]:
        response = await client.get(
            "/stats/operators",
            headers=auth_header(owner),
            params={"sort_by": "avg_score", "order": direction},
        )
        return [row["operator_id"] for row in response.json()]

    assert await order_of("asc") == [ids["weak"], ids["mid"], ids["strong"]]
    assert await order_of("desc") == [ids["strong"], ids["mid"], ids["weak"]]


@pytest.mark.asyncio
async def test_calls_sort_by_operator_is_alphabetical(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    names = ["Яременко", "Андрієнко", "Мельник"]
    for last in names:
        operator = await make_org_user(
            UserRole.OPERATOR, organization_id=owner.organization_id
        )
        async with async_session() as session:
            person = await session.get(User, operator.id)
            assert person is not None
            person.last_name = last
            session.add(
                Call(
                    audio_path=f"{last}.mp3",
                    organization_id=owner.organization_id,
                    operator_id=operator.id,
                    status=CallStatus.DONE,
                )
            )
            await session.commit()

    response = await client.get(
        "/calls",
        headers=auth_header(owner),
        params={"sort_by": "operator", "order": "asc", "limit": "100"},
    )
    shown = [
        item["operator_name"].split()[-1]
        for item in response.json()["items"]
        if item["operator_name"]
    ]

    assert [name for name in shown if name in names] == sorted(names, key=str.lower)


@pytest.mark.asyncio
async def test_calls_without_operator_stay_in_the_list_when_sorted_by_operator(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    async with async_session() as session:
        session.add(
            Call(
                audio_path="nobody.mp3",
                organization_id=owner.organization_id,
                status=CallStatus.QUEUED,
            )
        )
        await session.commit()

    response = await client.get(
        "/calls",
        headers=auth_header(owner),
        params={"sort_by": "operator", "order": "asc", "limit": "100"},
    )

    assert any(item["operator_name"] is None for item in response.json()["items"])
