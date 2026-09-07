import uuid
from collections.abc import AsyncGenerator, Sequence
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session
from app.integrations.llm.client import AnalysisResult
from app.models.calls import Call
from app.models.checklist import ChecklistItem
from app.models.transcripts import Transcript
from app.schemas.input.llm import CallAnalysis, ItemVerdict
from app.services.analysis import AnalysisService

WEIGHTS = {"greeting": "1.00", "needs": "2.00", "price_named": "3.00"}
REQUIRED = {"price_named"}


class StubAnalyzer:
    def __init__(self, verdicts: list[ItemVerdict]) -> None:
        self.verdicts = verdicts

    async def analyze(self, transcript, items, examples=()) -> AnalysisResult:
        return AnalysisResult(
            analysis=CallAnalysis(items=self.verdicts),
            model="stub",
            input_tokens=0,
            output_tokens=0,
            raw={"stub": True},
        )


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    created: list[int] = []

    async with async_session() as session:
        session.info["created_calls"] = created
        yield session

        await session.rollback()
        if created:
            await session.execute(delete(Call).where(Call.id.in_(created)))
            await session.commit()


async def make_checklist(session: AsyncSession) -> dict[str, ChecklistItem]:
    suffix = uuid.uuid4().hex[:8]
    items = {
        name: ChecklistItem(
            code=f"{name}_{suffix}",
            title=name,
            description="d",
            weight=Decimal(weight),
            is_required=name in REQUIRED,
        )
        for name, weight in WEIGHTS.items()
    }
    session.add_all(list(items.values()))
    await session.flush()
    return items


async def make_call(session: AsyncSession) -> int:
    call = Call(audio_path="x.mp3")
    session.add(call)
    await session.flush()
    session.add(Transcript(call_id=call.id, text="operator: алло", model="fixture"))
    await session.flush()
    session.info["created_calls"].append(call.id)
    return call.id


def verdict(item: ChecklistItem, passed: bool) -> ItemVerdict:
    return ItemVerdict(code=item.code, passed=passed, quote=None, confidence=1.0)


async def run_analysis(
    session: AsyncSession,
    call_id: int,
    items: Sequence[ChecklistItem],
    verdicts: list[ItemVerdict],
):
    service = AnalysisService(session=session, analyzer=StubAnalyzer(verdicts))
    service.checklist.get_active = lambda: _as_coroutine(items)  # type: ignore[method-assign]
    return await service.analyze_call(call_id)


async def _as_coroutine(value):
    return value


@pytest.mark.asyncio
async def test_score_uses_full_checklist_weight(session: AsyncSession) -> None:
    items = await make_checklist(session)
    call_id = await make_call(session)

    outcome = await run_analysis(
        session,
        call_id,
        list(items.values()),
        [
            verdict(items["greeting"], True),
            verdict(items["needs"], False),
            verdict(items["price_named"], True),
        ],
    )

    assert outcome.total_score == Decimal("66.67")
    assert outcome.missing_codes == []


@pytest.mark.asyncio
async def test_missing_verdict_does_not_inflate_score(session: AsyncSession) -> None:
    items = await make_checklist(session)
    call_id = await make_call(session)

    outcome = await run_analysis(
        session,
        call_id,
        list(items.values()),
        [verdict(items["greeting"], True), verdict(items["needs"], True)],
    )

    assert outcome.total_score == Decimal("50.00")
    assert outcome.missing_codes == [items["price_named"].code]
    assert outcome.failed_required == [items["price_named"].code]


@pytest.mark.asyncio
async def test_unknown_code_is_ignored(session: AsyncSession) -> None:
    items = await make_checklist(session)
    call_id = await make_call(session)

    outcome = await run_analysis(
        session,
        call_id,
        list(items.values()),
        [
            verdict(items["greeting"], True),
            ItemVerdict(code="not_in_checklist", passed=True, quote=None, confidence=1.0),
        ],
    )

    assert [score.passed for score in outcome.scores] == [True]
    assert outcome.total_score == Decimal("16.67")
