import enum
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.calls import Call


class Speaker(str, enum.Enum):
    OPERATOR = "operator"
    CLIENT = "client"
    UNKNOWN = "unknown"


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)

    call_id: Mapped[int] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default="uk")
    model: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), default=None)
    embedding_model: Mapped[str | None] = mapped_column(String(64), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    call: Mapped["Call"] = relationship(back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.idx",
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (UniqueConstraint("transcript_id", "idx", name="uq_segment_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        index=True,
    )

    idx: Mapped[int] = mapped_column()
    speaker: Mapped[Speaker] = mapped_column(
        Enum(
            Speaker,
            name="speaker",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=Speaker.UNKNOWN,
    )
    start_ms: Mapped[int] = mapped_column()
    end_ms: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)

    transcript: Mapped["Transcript"] = relationship(back_populates="segments")
