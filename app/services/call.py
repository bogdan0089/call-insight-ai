from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ColumnElement

from app.core.permissions import can_manage_people
from app.exceptions import EntityNotFound, PermissionDenied
from app.models.calls import Call, CallStatus
from app.models.users import User
from app.repositories.call import CallRepository
from app.repositories.scope import visible_operators
from app.repositories.user import UserRepository
from app.services.base_service import BaseService
from app.utils.storage import save_audio
from app.workers.tasks import process_call


class CallService(BaseService[Call, CallRepository]):
    entity_name = "Call"

    async def create_from_audio(
        self,
        actor: User,
        filename: str,
        content: bytes,
        operator_id: int | None = None,
        external_id: str | None = None,
    ) -> Call:
        operator_id = await self._resolve_operator(actor, operator_id)
        if external_id:
            existing = await self.repo.get_by_external_id(external_id)
            if existing is not None:
                return existing

        audio_path = await save_audio(filename=filename, content=content)

        call = Call(
            audio_path=audio_path,
            operator_id=operator_id,
            external_id=external_id,
            organization_id=actor.organization_id,
        )
        call = await self.repo.create(call)
        await self.session.commit()

        process_call.delay(call.id)
        return call

    async def list_calls(
        self,
        operator_id: int | None = None,
        status: CallStatus | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        score_min: Decimal | None = None,
        score_max: Decimal | None = None,
        limit: int = 20,
        offset: int = 0,
        scope: ColumnElement[bool] | None = None,
    ) -> tuple[Sequence[Call], int]:
        return await self.repo.list_calls(
            operator_id=operator_id,
            status=status,
            created_from=created_from,
            created_to=created_to,
            score_min=score_min,
            score_max=score_max,
            limit=limit,
            offset=offset,
            scope=scope,
        )

    async def get_report(
        self,
        call_id: int,
        scope: ColumnElement[bool] | None = None,
    ) -> Call:
        call = await self.repo.get_report(call_id, scope=scope)
        if call is None:
            raise EntityNotFound(entity=self.entity_name, id=call_id)
        return call

    async def _resolve_operator(self, actor: User, operator_id: int | None) -> int | None:
        """Resolve the call's operator within the actor's scope."""
        if not can_manage_people(actor):
            return actor.id

        if operator_id is None:
            return None

        users = UserRepository(self.session)
        target = await users.get_in_scope(operator_id, visible_operators(actor))
        if target is None:
            raise PermissionDenied("upload for this operator")

        return target.id
