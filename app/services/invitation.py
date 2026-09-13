from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import new_verification_token
from app.integrations.mail.client import Mailer, verification_email
from app.models.users import User
from app.models.verification import EmailVerification
from app.repositories.verification import EmailVerificationRepository

logger = get_logger(__name__)


class InvitationService:
    """Issue one-time links for email verification."""

    def __init__(
        self,
        session: AsyncSession,
        verifications: EmailVerificationRepository,
        mailer: Mailer,
    ) -> None:
        self.session = session
        self.verifications = verifications
        self.mailer = mailer

    async def send_verification(self, user: User) -> None:
        token = await self._issue(user)
        subject, body = verification_email(self._link("verify", token))
        await self._deliver(user, subject, body)
        logger.info("verification sent | user=%s", user.id)

    async def _deliver(self, user: User, subject: str, body: str) -> None:
        """Commit, then send; delivery failures are logged, not raised."""
        await self.session.commit()

        try:
            self.mailer.send(to=user.email, subject=subject, body=body)
        except Exception:
            logger.exception("mail not sent | user=%s | resend is available", user.id)

    async def _issue(self, user: User) -> str:
        token, token_hash = new_verification_token()
        await self.verifications.create(
            EmailVerification(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC)
                + timedelta(hours=settings.email_verification_ttl_hours),
            )
        )
        return token

    @staticmethod
    def _link(path: str, token: str) -> str:
        return f"{settings.frontend_url}/{path}?token={quote(token)}"
