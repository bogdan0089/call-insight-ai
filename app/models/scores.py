from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.calls import Call
    from app.models.checklist import ChecklistItem


class CallScore(Base):
    __tablename__ = "call_scores"
    __table_args__ = (
        UniqueConstraint("call_id", "checklist_item_id", name="uq_score_per_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"),
        index=True,
    )
    checklist_item_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_items.id", ondelete="CASCADE"),
        index=True,
    )

    passed: Mapped[bool] = mapped_column(Boolean)
    quote: Mapped[str | None] = mapped_column(Text, default=None)
    quote_start_ms: Mapped[int | None] = mapped_column(default=None)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    call: Mapped["Call"] = relationship(back_populates="scores")
    item: Mapped["ChecklistItem"] = relationship(back_populates="scores")
