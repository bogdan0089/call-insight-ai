from app.models.calls import Call
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
