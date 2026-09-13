import logging
import re
import smtplib
import ssl
from datetime import UTC, datetime
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

SSL_PORT = 465


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailer:
    """SMTP delivery; port 465 uses SMTPS, other ports use STARTTLS."""

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_header()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        if settings.smtp_port == SSL_PORT:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
                context=ssl.create_default_context(),
            ) as server:
                self._deliver(server, message)
            return

        with smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
        ) as server:
            if settings.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
            self._deliver(server, message)

    @staticmethod
    def _deliver(server: smtplib.SMTP, message: EmailMessage) -> None:
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)

    @staticmethod
    def _from_header() -> str | Address:
        name, address = parseaddr(settings.smtp_from)
        if "@" not in address:
            raise ValueError("SMTP_FROM must contain an email address")
        if not settings.smtp_from_name and not name:
            return address

        label = settings.smtp_from_name or name
        local, _, domain = address.partition("@")
        return Address(display_name=label, username=local, domain=domain)


class FileMailer:
    """Development delivery that writes each email to a file."""

    def send(self, to: str, subject: str, body: str) -> None:
        folder = Path(settings.mail_dir)
        folder.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", to)
        path = folder / f"{stamp}-{safe}.txt"
        path.write_text(f"To: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")

        logger.info("mail to %s | %s | %s", to, subject, path)


class LogMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        logger.info("mail to %s | %s\n%s", to, subject, body)


class QueuedMailer:
    """Enqueue delivery, sending inline if the queue is unavailable."""

    def send(self, to: str, subject: str, body: str) -> None:
        from app.workers.tasks import send_email

        try:
            send_email.delay(to, subject, body)
        except Exception:
            logger.exception("mail queue unavailable, sending inline | to=%s", to)
            build_transport().send(to, subject, body)


def build_transport() -> Mailer:
    """Mailer that performs delivery."""
    if settings.smtp_host:
        return SmtpMailer()
    if settings.mail_dir:
        return FileMailer()
    return LogMailer()


def build_mailer() -> Mailer:
    """Mailer used by the application."""
    if settings.mail_async:
        return QueuedMailer()
    return build_transport()


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
