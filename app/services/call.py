from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from app.exceptions import EntityNotFound
from app.models.calls import Call, CallStatus
from app.repositories.call import CallRepository
from app.services.base_service import BaseService
from app.utils.storage import save_audio
from app.workers.tasks import process_call


class CallService(BaseService[Call, CallRepository]):
    entity_name = "Call"

    async def create_from_audio(
        self,
        filename: str,
        content: bytes,
        operator_id: int | None = None,
        external_id: str | None = None,
    ) -> Call:
        if external_id:
            existing = await self.repo.get_by_external_id(external_id)
            if existing is not None:
                return existing

        audio_path = await save_audio(filename=filename, content=content)

        call = Call(
            audio_path=audio_path,
            operator_id=operator_id,
            external_id=external_id,
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
        )

    async def get_report(self, call_id: int) -> Call:
        call = await self.repo.get_report(call_id)
        if call is None:
            raise EntityNotFound(entity=self.entity_name, id=call_id)
        return call
