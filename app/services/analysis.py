import logging
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EntityNotFound
from app.integrations.llm.client import LLMAnalyzer
from app.models.ai_raw import AIResponseKind, RawAIResponse
from app.models.checklist import ChecklistItem
from app.models.scores import CallScore
from app.repositories.ai_raw import RawAIResponseRepository
from app.repositories.call import CallRepository
from app.repositories.checklist import ChecklistRepository
from app.repositories.score import CallScoreRepository
from app.repositories.transcript import TranscriptRepository
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

HUNDRED = Decimal("100")
CENTS = Decimal("0.01")


@dataclass(frozen=True)
class AnalysisOutcome:
    scores: Sequence[CallScore]
    total_score: Decimal
    failed_required: list[str]
    missing_codes: list[str]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    examples_used: int


class AnalysisService:
    def __init__(
        self,
        session: AsyncSession,
        analyzer: LLMAnalyzer,
        embeddings: EmbeddingService | None = None,
    ) -> None:
        self.session = session
        self.analyzer = analyzer
        self.embeddings = embeddings
        self.calls = CallRepository(session)
        self.checklist = ChecklistRepository(session)
        self.transcripts = TranscriptRepository(session)
        self.scores = CallScoreRepository(session)
        self.raw = RawAIResponseRepository(session)

    async def analyze_call(self, call_id: int) -> AnalysisOutcome:
        call = await self.calls.get(call_id)
        if call is None:
            raise EntityNotFound(entity="Call", call_id=call_id)

        transcript = await self.transcripts.get_by_call_id(call_id)
        if transcript is None:
            raise EntityNotFound(entity="Transcript", call_id=call_id)

        items = await self.checklist.get_active(call.organization_id)

        examples = (
            await self.embeddings.find_examples(call_id, call.organization_id)
            if self.embeddings
            else []
        )
        result = await self.analyzer.analyze(transcript.text, items, examples)

        await self.raw.create(
            RawAIResponse(
                call_id=call_id,
                kind=AIResponseKind.ANALYSIS,
                model=result.model,
                payload=result.raw,
            )
        )

        by_code = {item.code: item for item in items}
        await self.scores.delete_by_call_id(call_id)

        scores = [
            CallScore(
                call_id=call_id,
                checklist_item_id=by_code[verdict.code].id,
                passed=verdict.passed,
                quote=verdict.quote,
                confidence=Decimal(str(round(verdict.confidence, 2))),
            )
            for verdict in result.analysis.items
            if verdict.code in by_code
        ]
        self.session.add_all(scores)

        by_id = {item.id: item for item in items}
        scored_codes = {by_id[score.checklist_item_id].code for score in scores}
        missing_codes = [item.code for item in items if item.code not in scored_codes]
        if missing_codes:
            logger.warning(
                "call %s: model returned no verdict for %s, counting them as failed",
                call_id,
                ", ".join(missing_codes),
            )

        total_score = self._weighted_score(scores, items, by_id)
        failed_required = [
            item.code
            for item in items
            if item.is_required
            and (
                item.code in missing_codes
                or any(
                    not score.passed and score.checklist_item_id == item.id
                    for score in scores
                )
            )
        ]

        call.total_score = total_score
        await self.session.commit()

        return AnalysisOutcome(
            scores=scores,
            total_score=total_score,
            failed_required=failed_required,
            missing_codes=missing_codes,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            examples_used=len(examples),
        )

    @staticmethod
    def _weighted_score(
        scores: Sequence[CallScore],
        items: Sequence[ChecklistItem],
        by_id: dict[int, ChecklistItem],
    ) -> Decimal:
        total_weight = sum(item.weight for item in items)
        if not total_weight:
            return Decimal("0.00")

        earned = sum(
            by_id[score.checklist_item_id].weight for score in scores if score.passed
        )
        return (earned / total_weight * HUNDRED).quantize(CENTS, rounding=ROUND_HALF_UP)
