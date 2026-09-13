import uuid
from email.headerregistry import Address
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session
from app.integrations.mail import client as mail
from app.models.users import User
from app.workers import tasks


def registration(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": "secret123",
        "first_name": "Test",
        "last_name": "Mail",
        "organization_name": "Mail check",
    }


@pytest.mark.parametrize(
    ("smtp_host", "mail_dir", "expected"),
    [
        ("smtp.example.com", "storage/mail", mail.SmtpMailer),
        ("", "storage/mail", mail.FileMailer),
        ("", "", mail.LogMailer),
    ],
)
def test_transport_follows_settings(
    monkeypatch: pytest.MonkeyPatch,
    smtp_host: str,
    mail_dir: str,
    expected: type,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", smtp_host)
    monkeypatch.setattr(settings, "mail_dir", mail_dir)

    assert isinstance(mail.build_transport(), expected)


def test_async_setting_queues_mail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mail_async", True)

    assert isinstance(mail.build_mailer(), mail.QueuedMailer)


def test_file_mailer_writes_the_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(settings, "mail_dir", str(tmp_path))

    mail.FileMailer().send(to="a@example.com", subject="Hello", body="Link inside")

    [written] = tmp_path.iterdir()
    content = written.read_text(encoding="utf-8")
    assert "To: a@example.com" in content
    assert "Subject: Hello" in content
    assert "Link inside" in content


def test_queue_outage_falls_back_to_inline_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delivered: list[str] = []

    class Transport:
        def send(self, to: str, subject: str, body: str) -> None:
            delivered.append(to)

    def broken_delay(*args: object) -> None:
        raise ConnectionError("broker is down")

    monkeypatch.setattr(tasks.send_email, "delay", broken_delay)
    monkeypatch.setattr(mail, "build_transport", lambda: Transport())

    mail.QueuedMailer().send(to="b@example.com", subject="Hi", body="Body")

    assert delivered == ["b@example.com"]


def test_sender_name_is_added_to_the_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_from", "no-reply@example.com")
    monkeypatch.setattr(settings, "smtp_from_name", "call insight")

    header = mail.SmtpMailer._from_header()

    assert isinstance(header, Address)
    assert header.addr_spec == "no-reply@example.com"
    assert header.display_name == "call insight"


def test_sender_without_an_address_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_from", "call insight")

    with pytest.raises(ValueError):
        mail.SmtpMailer._from_header()


@pytest.mark.asyncio
async def test_mail_failure_does_not_undo_registration(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenMailer:
        def send(self, to: str, subject: str, body: str) -> None:
            raise OSError("smtp is down")

    monkeypatch.setattr("app.api.deps.build_mailer", lambda: BrokenMailer())
    email = f"mailfail{uuid.uuid4().hex[:8]}@example.com"

    response = await client.post("/auth/register", json=registration(email))

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.email == email))

    assert response.status_code == 202
    assert user is not None
