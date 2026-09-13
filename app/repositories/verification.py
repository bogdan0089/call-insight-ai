from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.verification import EmailVerification
from app.repositories.base_repository import SqlalchemyAsyncRepository


class EmailVerificationRepository(SqlalchemyAsyncRepository[EmailVerification]):
    model = EmailVerification

    async def get_pending(self, token_hash: str) -> EmailVerification | None:
        stmt = (
            select(EmailVerification)
            .where(
                EmailVerification.token_hash == token_hash,
                EmailVerification.used_at.is_(None),
                EmailVerification.expires_at > datetime.now(UTC),
            )
            .options(selectinload(EmailVerification.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def invalidate_for_user(self, user_id: int) -> None:
        await self.session.execute(
            update(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
