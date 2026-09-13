import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.calls import Call
    from app.models.organizations import Organization
    from app.models.verification import EmailVerification


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=UserRole.OPERATOR,
        index=True
    )
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    calls: Mapped[list["Call"]] = relationship(back_populates="operator")
    organization: Mapped["Organization | None"] = relationship(back_populates="users")
    manager: Mapped["User | None"] = relationship(
        remote_side="User.id",
        back_populates="operators",
    )
    operators: Mapped[list["User"]] = relationship(back_populates="manager")
    verifications: Mapped[list["EmailVerification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def manager_name(self) -> str | None:
        manager = self.__dict__.get("manager")
        return manager.full_name if manager is not None else None
