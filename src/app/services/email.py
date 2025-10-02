"""Email utility helpers for transactional messages."""

from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional
from urllib import error, request

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when email delivery fails permanently."""


@dataclass
class EmailConfig:
    """Configuration discovered from environment variables."""

    provider: str
    from_email: str
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    message_stream: Optional[str] = None
    timeout: int = 10


def _load_email_config() -> EmailConfig:
    """Load configuration for either Postmark or SMTP providers."""

    from_email = (
        os.getenv("POSTMARK_FROM_EMAIL")
        or os.getenv("SMTP_FROM_EMAIL")
        or os.getenv("EMAIL_FROM")
        or "no-reply@sensasiwangi.id"
    )

    if os.getenv("POSTMARK_API_TOKEN"):
        return EmailConfig(
            provider="postmark",
            from_email=from_email,
            message_stream=os.getenv("POSTMARK_MESSAGE_STREAM"),
            timeout=int(os.getenv("EMAIL_TIMEOUT", "10")),
        )

    if os.getenv("SMTP_HOST"):
        return EmailConfig(
            provider="smtp",
            from_email=from_email,
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() != "false",
            timeout=int(os.getenv("EMAIL_TIMEOUT", "10")),
        )

    return EmailConfig(provider="console", from_email=from_email)


def _build_verification_link(token_or_link: str) -> str:
    """Convert a token into an absolute verification URL when possible."""

    if token_or_link.startswith("http://") or token_or_link.startswith("https://"):
        return token_or_link

    base_url = (
        os.getenv("EMAIL_VERIFICATION_BASE_URL")
        or os.getenv("FRONTEND_BASE_URL")
        or os.getenv("APP_BASE_URL")
    )

    if base_url:
        return f"{base_url.rstrip('/')}/verify-email?token={token_or_link}"

    return token_or_link


def _compose_message(config: EmailConfig, recipient: str, verification_link: str) -> EmailMessage:
    """Create an email message with both text and HTML content."""

    message = EmailMessage()
    message["Subject"] = "Verifikasi email Sensasiwangi.id"
    message["From"] = config.from_email
    message["To"] = recipient

    text_body = (
        "Halo,\n\n"
        "Terima kasih telah mendaftar di Sensasiwangi.id. "
        "Klik tautan berikut untuk mengaktifkan akun Anda:\n"
        f"{verification_link}\n\n"
        "Jika Anda tidak merasa mendaftar, abaikan email ini.\n"
    )

    html_body = f"""
    <p>Halo,</p>
    <p>Terima kasih telah mendaftar di <strong>Sensasiwangi.id</strong>.</p>
    <p>
      Silakan klik tautan berikut untuk mengaktifkan akun Anda:<br />
      <a href=\"{verification_link}\">Verifikasi alamat email</a>
    </p>
    <p>Jika Anda tidak merasa mendaftar, abaikan email ini.</p>
    """

    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _send_via_postmark(config: EmailConfig, message: EmailMessage) -> None:
    payload = {
        "From": message["From"],
        "To": message["To"],
        "Subject": message["Subject"],
        "TextBody": message.get_body(preferencelist=("plain",)).get_content(),
        "HtmlBody": message.get_body(preferencelist=("html",)).get_content(),
    }
    if config.message_stream:
        payload["MessageStream"] = config.message_stream

    data = json.dumps(payload).encode("utf-8")
    req = request.Request("https://api.postmarkapp.com/email", data=data, method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Postmark-Server-Token", os.getenv("POSTMARK_API_TOKEN", ""))

    try:
        with request.urlopen(req, timeout=config.timeout) as response:
            if response.status >= 400:
                raise EmailDeliveryError(f"Postmark returned status {response.status}")
    except error.HTTPError as exc:
        raise EmailDeliveryError(f"Postmark request failed: {exc.status}") from exc
    except error.URLError as exc:
        raise EmailDeliveryError(f"Unable to reach Postmark API: {exc.reason}") from exc


def _send_via_smtp(config: EmailConfig, message: EmailMessage) -> None:
    if not config.smtp_host:
        raise EmailDeliveryError("SMTP host is not configured")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=config.timeout) as smtp:
            if config.smtp_use_tls:
                smtp.starttls(context=context)
            if config.smtp_username and config.smtp_password:
                smtp.login(config.smtp_username, config.smtp_password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryError(f"SMTP delivery failed: {exc}") from exc


def send_verification_email(recipient: str, token_or_link: str) -> None:
    """Send a verification email using configured provider.

    When no provider is configured the message is logged so that local tests can
    still observe the outgoing payload.
    """

    config = _load_email_config()
    verification_link = _build_verification_link(token_or_link)
    message = _compose_message(config, recipient, verification_link)

    try:
        if config.provider == "postmark":
            _send_via_postmark(config, message)
            logger.info("Verification email sent via Postmark to %s", recipient)
        elif config.provider == "smtp":
            _send_via_smtp(config, message)
            logger.info("Verification email sent via SMTP to %s", recipient)
        else:
            logger.info(
                "Verification email to %s would be sent with link: %s", recipient, verification_link
            )
    except EmailDeliveryError as exc:
        logger.warning("Failed to deliver verification email to %s: %s", recipient, exc)

