from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.integrations.embeddings.client import build_embedder
from app.repositories.call import CallRepository
from app.services.call import CallService
from app.services.embedding import EmbeddingService


def get_call_service(session: AsyncSession = Depends(get_session)) -> CallService:
    return CallService(repo=CallRepository(session), session=session)


def get_embedding_service(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingService:
    return EmbeddingService(session=session, embedder=build_embedder())
