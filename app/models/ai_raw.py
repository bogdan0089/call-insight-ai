import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.calls import Call


class AIResponseKind(str, enum.Enum):
    TRANSCRIPTION = "transcription"
    ANALYSIS = "analysis"


class RawAIResponse(Base):
    __tablename__ = "raw_ai_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"),
        index=True,
    )

    kind: Mapped[AIResponseKind] = mapped_column(
        Enum(
            AIResponseKind,
            name="ai_response_kind",
            values_callable=lambda e: [m.value for m in e],
        ),
        index=True,
    )
    model: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    call: Mapped["Call"] = relationship(back_populates="raw_responses")
