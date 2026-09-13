import logging
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class LogMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        logger.info("mail to %s | %s\n%s", to, subject, body)


def build_mailer() -> Mailer:
    return LogMailer()


def verification_email(link: str) -> tuple[str, str]:
    subject = "Підтвердіть пошту — call insight"
    body = (
        "Вітаємо!\n\n"
        "Щоб завершити реєстрацію, перейдіть за посиланням:\n"
        f"{link}\n\n"
        f"Посилання діє {settings.email_verification_ttl_hours} год. "
        "Якщо ви не реєструвались — просто проігноруйте цей лист."
    )
    return subject, body


def invitation_email(organization_name: str, link: str) -> tuple[str, str]:
    subject = f"Запрошення до {organization_name} — call insight"
    body = (
        f"Вас додали до команди «{organization_name}».\n\n"
        "Щоб увійти, задайте собі пароль за посиланням:\n"
        f"{link}\n\n"
        f"Посилання діє {settings.email_verification_ttl_hours} год."
    )
    return subject, body
