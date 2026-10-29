import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ENV = os.getenv("APP_ENV", "development")
URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")
SECRET = os.getenv("JWT_SECRET", "")
if len(SECRET) < 32:
    raise RuntimeError("Set JWT_SECRET to at least 32 random characters in .env.")
if ENV == "production" and (
    not URL.startswith("https://") or not os.getenv("SMTP_HOST")
):
    raise RuntimeError("Production requires an HTTPS APP_URL and SMTP_HOST.")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./predictpro.db")
COOKIE = "__Host-predictpro" if ENV == "production" else "predictpro"
SECURE = ENV == "production"
HOSTS = [
    x.strip()
    for x in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if x.strip()
]
