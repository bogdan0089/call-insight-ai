import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session
from app.integrations.embeddings.client import FakeEmbedder
from app.models.calls import Call, CallStatus
from app.models.checklist import ChecklistItem
from app.models.scores import CallScore
from app.models.transcripts import Transcript
from app.services.embedding import EmbeddingService

TEXT = "operator: добрий день, мене звати Олег. client: скільки коштує?"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
        await session.rollback()


async def add_scored_call(
    session: AsyncSession,
    embedder: FakeEmbedder,
    item: ChecklistItem,
    is_verified: bool,
) -> int:
    call = Call(audio_path="x.mp3", status=CallStatus.DONE)
    session.add(call)
    await session.flush()

    session.add(
        Transcript(
            call_id=call.id,
            text=TEXT,
            model="fixture",
            embedding=await embedder.embed(TEXT),
            embedding_model=embedder.model_name,
        )
    )
    session.add(
        CallScore(
            call_id=call.id,
            checklist_item_id=item.id,
            passed=True,
            is_verified=is_verified,
        )
    )
    await session.flush()
    return call.id


@pytest.mark.asyncio
async def test_find_examples_skips_unverified_calls(session: AsyncSession) -> None:
    embedder = FakeEmbedder()

    item = ChecklistItem(code=f"greeting_{uuid.uuid4().hex[:8]}", title="t", description="d")
    session.add(item)
    await session.flush()

    verified_id = await add_scored_call(session, embedder, item, is_verified=True)
    unverified_id = await add_scored_call(session, embedder, item, is_verified=False)

    target = Call(audio_path="target.mp3", status=CallStatus.QUEUED)
    session.add(target)
    await session.flush()
    session.add(
        Transcript(
            call_id=target.id,
            text=TEXT,
            model="fixture",
            embedding=await embedder.embed(TEXT),
            embedding_model=embedder.model_name,
        )
    )
    await session.flush()

    examples = await EmbeddingService(session=session, embedder=embedder).find_examples(
        target.id, organization_id=None, limit=10
    )
    found_ids = [example.call_id for example in examples]

    assert verified_id in found_ids
    assert unverified_id not in found_ids
    assert target.id not in found_ids


@pytest.mark.asyncio
async def test_example_carries_only_verified_verdicts(session: AsyncSession) -> None:
    embedder = FakeEmbedder()

    verified_item = ChecklistItem(
        code=f"greeting_{uuid.uuid4().hex[:8]}", title="t", description="d"
    )
    other_item = ChecklistItem(
        code=f"price_{uuid.uuid4().hex[:8]}", title="t", description="d"
    )
    session.add_all([verified_item, other_item])
    await session.flush()

    call_id = await add_scored_call(session, embedder, verified_item, is_verified=True)
    session.add(
        CallScore(
            call_id=call_id,
            checklist_item_id=other_item.id,
            passed=False,
            is_verified=False,
        )
    )
    await session.flush()

    target = Call(audio_path="target.mp3", status=CallStatus.QUEUED)
    session.add(target)
    await session.flush()
    session.add(
        Transcript(
            call_id=target.id,
            text=TEXT,
            model="fixture",
            embedding=await embedder.embed(TEXT),
            embedding_model=embedder.model_name,
        )
    )
    await session.flush()

    examples = await EmbeddingService(session=session, embedder=embedder).find_examples(
        target.id, organization_id=None, limit=10
    )
    example = next(item for item in examples if item.call_id == call_id)

    assert [verdict.code for verdict in example.verdicts] == [verified_item.code]


@pytest.mark.asyncio
async def test_find_examples_returns_empty_without_transcript(session: AsyncSession) -> None:
    call = Call(audio_path="x.mp3", status=CallStatus.QUEUED)
    session.add(call)
    await session.flush()

    examples = await EmbeddingService(
        session=session, embedder=FakeEmbedder()
    ).find_examples(call.id, organization_id=None)

    assert examples == []
