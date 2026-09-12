from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.integrations.embeddings.client import build_embedder
from app.repositories.call import CallRepository
from app.repositories.score import CallScoreRepository
from app.repositories.stats import StatsRepository
from app.services.call import CallService
from app.services.embedding import EmbeddingService
from app.services.score import CallScoreService
from app.services.stats import StatsService


def get_call_service(session: AsyncSession = Depends(get_session)) -> CallService:
    return CallService(repo=CallRepository(session), session=session)


def get_embedding_service(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingService:
    return EmbeddingService(session=session, embedder=build_embedder())


def get_score_service(session: AsyncSession = Depends(get_session)) -> CallScoreService:
    return CallScoreService(repo=CallScoreRepository(session), session=session)


def get_stats_service(session: AsyncSession = Depends(get_session)) -> StatsService:
    return StatsService(repo=StatsRepository(session), session=session)
