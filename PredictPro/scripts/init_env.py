"""Create local configuration once without overwriting existing secrets."""

from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env already exists; leaving it unchanged.")
else:
    content = (
        (root / ".env.example")
        .read_text()
        .replace("JWT_SECRET=\n", "JWT_SECRET=" + secrets.token_hex(32) + "\n")
    )
    target.write_text(content)
    target.chmod(0o600)
    print(
        "Created .env with a fresh signing secret. Review configuration before production."
    )
