from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.organizations import Organization
    from app.models.scores import CallScore


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_checklist_code_per_org"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    organization: Mapped["Organization | None"] = relationship(
        back_populates="checklist_items"
    )
    scores: Mapped[list["CallScore"]] = relationship(back_populates="item")
