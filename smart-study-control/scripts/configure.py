"""Generate development config without printing secrets. Never overwrites an existing .env."""
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env already exists; leaving it unchanged")
text = (root / ".env.example").read_text()
text = text.replace("replace-with-generated-secret-at-least-32-characters", secrets.token_urlsafe(48))
text = text.replace("replace-with-generated-database-password", secrets.token_urlsafe(32))
text = text.replace("TELEGRAM_WEBHOOK_SECRET=\n", "TELEGRAM_WEBHOOK_SECRET=" + secrets.token_urlsafe(32) + "\n")
target.write_text(text)
target.chmod(0o600)
print("Development configuration created")
