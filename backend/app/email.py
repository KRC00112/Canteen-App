"""Send emails: Brevo HTTP API in production, SMTP locally, or the server log for testing."""
import json
import logging
import smtplib
import sys
import urllib.error
import urllib.request
from email.message import EmailMessage

from app.config import (
    BREVO_API_KEY,
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)

log = logging.getLogger("canteen.email")
if not log.handlers:
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.INFO)
    log.propagate = False


class EmailError(Exception):
    pass


def provider() -> str:
    if BREVO_API_KEY and EMAIL_FROM:
        return "brevo"
    if SMTP_HOST and EMAIL_FROM:
        return "smtp"
    return "log"


def send_email(to: str, subject: str, text: str, html: str) -> None:
    """Raises EmailError if the email could not be sent."""
    kind = provider()
    if kind == "brevo":
        _send_brevo(to, subject, text, html)
    elif kind == "smtp":
        _send_smtp(to, subject, text, html)
    else:
        # No email provider configured: print it so it can still be tested.
        log.info(f"[EMAIL not sent - no provider configured] to={to} subject={subject!r}\n{text}")


def _send_brevo(to: str, subject: str, text: str, html: str) -> None:
    body = {
        "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
        "htmlContent": html,
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(body).encode(),
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status >= 300:
                raise EmailError(f"Brevo returned {resp.status}")
    except urllib.error.HTTPError as e:
        log.info(f"[EMAIL failed] Brevo {e.code}: {e.read()[:300]!r}")
        raise EmailError(f"Brevo returned {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        log.info(f"[EMAIL failed] Brevo unreachable: {e}")
        raise EmailError("Email service unreachable") from e


def _send_smtp(to: str, subject: str, text: str, html: str) -> None:
    msg = EmailMessage()
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            if SMTP_USER:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        log.info(f"[EMAIL failed] SMTP: {e}")
        raise EmailError("Email could not be sent") from e
