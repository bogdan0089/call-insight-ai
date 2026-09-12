from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.calls import Call, CallStatus
from app.models.scores import CallScore
from app.models.transcripts import Speaker, TranscriptSegment


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idx: int
    speaker: Speaker
    start_ms: int
    end_ms: int
    text: str


class ScoreOut(BaseModel):
    id: int
    checklist_item_id: int
    code: str
    title: str
    weight: Decimal
    is_required: bool
    passed: bool
    quote: str | None
    quote_start_ms: int | None
    confidence: Decimal | None
    is_verified: bool

    @classmethod
    def from_model(cls, score: CallScore) -> "ScoreOut":
        return cls(
            id=score.id,
            checklist_item_id=score.checklist_item_id,
            code=score.item.code,
            title=score.item.title,
            weight=score.item.weight,
            is_required=score.item.is_required,
            passed=score.passed,
            quote=score.quote,
            quote_start_ms=score.quote_start_ms,
            confidence=score.confidence,
            is_verified=score.is_verified,
        )


class CallReport(BaseModel):
    id: int
    external_id: str | None
    operator_id: int | None
    operator_name: str | None
    status: CallStatus
    duration_sec: int | None
    total_score: Decimal | None
    error: str | None
    created_at: datetime

    failed_required: bool
    verified_count: int

    transcript_text: str | None
    segments: list[SegmentOut]
    scores: list[ScoreOut]

    @classmethod
    def from_model(cls, call: Call) -> "CallReport":
        scores = sorted(call.scores, key=lambda s: s.item.code)
        segments: list[TranscriptSegment] = (
            list(call.transcript.segments) if call.transcript is not None else []
        )
        return cls(
            id=call.id,
            external_id=call.external_id,
            operator_id=call.operator_id,
            operator_name=call.operator_name,
            status=call.status,
            duration_sec=call.duration_sec,
            total_score=call.total_score,
            error=call.error,
            created_at=call.created_at,
            failed_required=any(
                not s.passed and s.item.is_required for s in call.scores
            ),
            verified_count=sum(1 for s in call.scores if s.is_verified),
            transcript_text=call.transcript.text if call.transcript else None,
            segments=[SegmentOut.model_validate(s) for s in segments],
            scores=[ScoreOut.from_model(s) for s in scores],
        )
