from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.repositories.call import CallRepository
from app.services.call import CallService


def get_call_service(session: AsyncSession = Depends(get_session)) -> CallService:
    return CallService(repo=CallRepository(session))
