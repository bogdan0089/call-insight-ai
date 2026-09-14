from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_people_service, require
from app.core.permissions import can_manage_people
from app.models.users import User
from app.schemas.input.people import InviteRequest, PeopleQuery, PersonUpdate
from app.schemas.output.people import PeoplePage, PersonOut
from app.services.people import PeopleService

router = APIRouter(prefix="/people", tags=["people"])

Manager = Depends(require(can_manage_people, "manage people"))


@router.get("", response_model=PeoplePage)
async def list_people(
    query: Annotated[PeopleQuery, Query()],
    service: PeopleService = Depends(get_people_service),
    actor: User = Manager,
) -> PeoplePage:
    people, total = await service.list_people(actor=actor, **query.model_dump())
    return PeoplePage(
        items=[PersonOut.model_validate(person) for person in people],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PersonOut)
async def invite_person(
    payload: InviteRequest,
    service: PeopleService = Depends(get_people_service),
    actor: User = Manager,
) -> PersonOut:
    person = await service.invite(actor=actor, **payload.model_dump())
    return PersonOut.model_validate(person)


@router.patch("/{person_id}", response_model=PersonOut)
async def update_person(
    person_id: int,
    payload: PersonUpdate,
    service: PeopleService = Depends(get_people_service),
    actor: User = Manager,
) -> PersonOut:
    person = await service.update(
        actor=actor, person_id=person_id, **payload.model_dump()
    )
    return PersonOut.model_validate(person)
