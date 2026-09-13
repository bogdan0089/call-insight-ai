import asyncio
from collections.abc import Coroutine
from typing import Any

from celery.utils.log import get_task_logger

from app.core.config import settings
from app.core.db import async_session, engine
from app.fixtures.dialogues import DIALOGUES
from app.integrations.embeddings.client import build_embedder
from app.integrations.llm.client import AnthropicAnalyzer, FakeAnalyzer, LLMAnalyzer
from app.integrations.mail.client import build_transport
from app.models.calls import CallStatus
from app.models.transcripts import Transcript, TranscriptSegment
from app.repositories.call import CallRepository
from app.repositories.transcript import TranscriptRepository
from app.services.analysis import AnalysisService
from app.services.embedding import EmbeddingService
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)

SEGMENT_MS = 4000


def build_analyzer(call_id: int) -> LLMAnalyzer:
    if settings.anthropic_api_key:
        return AnthropicAnalyzer()

    dialogue = DIALOGUES[call_id % len(DIALOGUES)]
    logger.warning("no anthropic key, using FakeAnalyzer for call %s", call_id)
    return FakeAnalyzer(dialogue["expected_passed"])


def run_task(coro: Coroutine[Any, Any, None]) -> None:
    """Run a coroutine in its own event loop and dispose the engine."""

    async def runner() -> None:
        try:
            await coro
        finally:
            await engine.dispose()

    asyncio.run(runner())


@celery_app.task(name="send_email", bind=True, max_retries=5)
def send_email(self, to: str, subject: str, body: str) -> None:
    """Deliver an email, retrying with a growing delay."""
    try:
        build_transport().send(to, subject, body)
    except Exception as exc:
        logger.warning("mail to %s failed: %s", to, exc)
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1)) from exc


@celery_app.task(name="process_call", bind=True, max_retries=3)
def process_call(self, call_id: int) -> None:
    try:
        run_task(_process_call(call_id))
    except Exception as exc:
        logger.exception("call %s failed", call_id)
        run_task(_mark_failed(call_id, str(exc)))
        raise self.retry(exc=exc, countdown=30) from exc


async def _process_call(call_id: int) -> None:
    async with async_session() as session:
        call_repo = CallRepository(session)
        transcript_repo = TranscriptRepository(session)

        call = await call_repo.get(call_id)
        if call is None:
            logger.warning("call %s not found", call_id)
            return

        if call.status == CallStatus.DONE:
            logger.info("call %s already processed", call_id)
            return

        call.status = CallStatus.TRANSCRIBING
        call.error = None
        await session.commit()

        existing = await transcript_repo.get_by_call_id(call_id)
        if existing is None:
            transcript = _build_transcript(call_id)
            await transcript_repo.create(transcript)
            logger.info("call %s transcribed into %s segments", call_id, len(transcript.segments))

        embedding = EmbeddingService(session=session, embedder=build_embedder())
        await embedding.embed_transcript(call_id)

        call.status = CallStatus.ANALYZING
        await session.commit()

        analysis = AnalysisService(
            session=session,
            analyzer=build_analyzer(call_id),
            embeddings=embedding,
        )
        outcome = await analysis.analyze_call(call_id)
        logger.info(
            "call %s scored %s, failed required: %s, examples %s, tokens %s/%s, cost $%.4f",
            call_id,
            outcome.total_score,
            outcome.failed_required or "none",
            outcome.examples_used,
            outcome.input_tokens,
            outcome.output_tokens,
            outcome.cost_usd,
        )

        call.status = CallStatus.DONE
        call.duration_sec = _duration(call_id)
        await session.commit()


def _build_transcript(call_id: int) -> Transcript:
    dialogue = DIALOGUES[call_id % len(DIALOGUES)]

    segments = [
        TranscriptSegment(
            idx=idx,
            speaker=speaker,
            start_ms=idx * SEGMENT_MS,
            end_ms=(idx + 1) * SEGMENT_MS,
            text=text,
        )
        for idx, (speaker, text) in enumerate(dialogue["segments"])
    ]

    return Transcript(
        call_id=call_id,
        text="\n".join(f"{speaker.value}: {text}" for speaker, text in dialogue["segments"]),
        language="uk",
        model="fixture",
        segments=segments,
    )


def _duration(call_id: int) -> int:
    dialogue = DIALOGUES[call_id % len(DIALOGUES)]
    return len(dialogue["segments"]) * SEGMENT_MS // 1000


async def _mark_failed(call_id: int, error: str) -> None:
    async with async_session() as session:
        repo = CallRepository(session)

        call = await repo.get(call_id)
        if call is None:
            return

        call.status = CallStatus.FAILED
        call.error = error[:1000]
        await session.commit()
