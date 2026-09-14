"""Send a test email: python -m app.integrations.mail.check you@example.com"""

import smtplib
import sys

from app.core.config import settings
from app.integrations.mail.client import SSL_PORT, build_transport


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.integrations.mail.check you@example.com")
        return 2

    to = sys.argv[1]
    transport = build_transport()
    print(f"Transport: {type(transport).__name__}")
    if settings.smtp_host:
        if settings.smtp_port == SSL_PORT:
            mode = "SMTPS"
        else:
            mode = "STARTTLS" if settings.smtp_use_tls else "plain"
        print(f"Server: {settings.smtp_host}:{settings.smtp_port} ({mode})")
        print(f"Login: {settings.smtp_user or 'none'}")
        print(f"From: {settings.smtp_from}")
    else:
        print(f"SMTP_HOST is empty, mail goes to {settings.mail_dir or 'the log'}")

    try:
        transport.send(
            to=to,
            subject="Mail check - call insight",
            body="If you can read this, sending works.",
        )
    except smtplib.SMTPAuthenticationError as exc:
        print(f"\nLogin rejected: {exc.smtp_code} {exc.smtp_error!r}")
        print("Gmail requires an app password, not the account password.")
        return 1
    except smtplib.SMTPNotSupportedError as exc:
        print(f"\nServer does not support authentication: {exc}")
        print("Leave SMTP_USER and SMTP_PASSWORD empty for servers without auth, e.g. mailpit.")
        return 1
    except (smtplib.SMTPException, OSError) as exc:
        print(f"\nSend failed: {type(exc).__name__}: {exc}")
        print("Check host and port: 465 is SMTPS, 587 is STARTTLS.")
        return 1

    print(f"\nSent to {to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
