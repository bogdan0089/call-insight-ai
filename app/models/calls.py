import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func

from app.core.db import Base

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.ai_raw import RawAIResponse
    from app.models.scores import CallScore
    from app.models.transcripts import Transcript
    from app.models.users import User



class CallStatus(str, enum.Enum):
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    DONE = "done"
    FAILED = "failed"


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True
    )
    status: Mapped[CallStatus] = mapped_column(
        Enum(
            CallStatus,
            name="call_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=CallStatus.QUEUED,
        server_default=CallStatus.QUEUED.value,
        index=True
    )
    audio_path: Mapped[str] = mapped_column(String(512))
    duration_sec: Mapped[int | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    total_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    operator: Mapped["User | None"] = relationship(back_populates="calls")

    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="call",
        uselist=False,
        cascade="all, delete-orphan"
    )

    scores: Mapped[list["CallScore"]] = relationship(
        back_populates="call",
        cascade="all, delete-orphan"
    )

    raw_responses: Mapped[list["RawAIResponse"]] = relationship(
        back_populates="call",
        cascade="all, delete-orphan"
    )



