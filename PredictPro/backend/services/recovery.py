import json
import os
import secrets
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote
from sqlalchemy import update
from backend.config import URL, ENV, ROOT
from backend.models.entities import Reset, now
from backend.utils.security import digest


def create_reset(db, user):
    db.execute(update(Reset).where(Reset.user_id == user.id).values(used=True))
    token = secrets.token_urlsafe(32)
    db.add(
        Reset(
            user_id=user.id,
            digest=digest(token),
            expires_at=now() + timedelta(minutes=30),
        )
    )
    return f"{URL}/#reset?token={quote(token)}"


def send_reset(email, link):
    message = EmailMessage()
    message["Subject"] = "Reset your PredictPro password"
    message["From"] = os.getenv("SMTP_FROM", "noreply@predictpro.local")
    message["To"] = email
    message.set_content(
        f"Use this one-time link within 30 minutes:\n{link}\nIf you did not request this, ignore this email."
    )
    host = os.getenv("SMTP_HOST")
    if host:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
            if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                smtp.starttls()
            if os.getenv("SMTP_USERNAME"):
                smtp.login(os.environ["SMTP_USERNAME"], os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(message)
    elif ENV != "production":
        folder = ROOT / "backend" / "outbox"
        folder.mkdir(mode=0o700, exist_ok=True)
        path = folder / (secrets.token_hex(12) + ".eml")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(str(message))
    else:
        raise RuntimeError("SMTP is not configured.")
