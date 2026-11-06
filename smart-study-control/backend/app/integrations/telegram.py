"""Telegram HTTPS transport. Tokens, OTPs and complete request URLs are never logged."""

import secrets
import httpx
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.models.entities import AuthChallenge, TelegramIdentity, TelegramUpdate, User, now
from app.services.challenges import lock_challenge, otp_hash
from app.security.auth import digest


class TelegramTransport:
    def call(self, method, payload=None):
        if not settings.telegram_token:
            raise HTTPException(503, "Telegram bot serverda sozlanmagan")
        try:
            with httpx.Client(timeout=35) as client:
                response = client.post(
                    "https://api.telegram.org/bot" + settings.telegram_token + "/" + method,
                    json=payload or {},
                )
                response.raise_for_status()
                body = response.json()
                if body.get("ok") is not True:
                    raise ValueError("Telegram rejected request")
                return body["result"]
        except (httpx.HTTPError, ValueError, KeyError):
            raise HTTPException(503, "Telegram vaqtincha ishlamayapti; qayta urinib ko‘ring")

    def send(self, chat_id, text):
        return self.call("sendMessage", {"chat_id": chat_id, "text": text, "protect_content": True})


transport = TelegramTransport()


def process_update(db, update):
    ident = update.get("update_id")
    if type(ident) is not int:
        return
    if db.scalar(select(TelegramUpdate.id).where(TelegramUpdate.update_id == str(ident))):
        return
    # Inserting first reserves exactly this Telegram update across poll/webhook workers.
    db.add(TelegramUpdate(update_id=str(ident)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return
    message = update.get("message", {})
    chat, sender = message.get("chat", {}), message.get("from", {})
    text = message.get("text", "")
    if chat.get("type") != "private" or sender.get("is_bot") or str(chat.get("id")) != str(sender.get("id")):
        return
    parts = text.split()
    if len(parts) != 2 or parts[0].split("@")[0] != "/start" or not parts[1].startswith(("login_", "link_")):
        return
    kind, state = parts[1].split("_", 1)
    row = db.scalar(select(AuthChallenge).where(AuthChallenge.state_hash == digest(state)))
    if not row:
        return
    row = lock_challenge(db, row.id)
    user = db.get(User, row.user_id)
    if (
        row.kind != ("TG_LOGIN" if kind == "login" else "TG_LINK")
        or row.consumed
        or row.expires_at <= now()
        or row.attempts >= 5
        or row.delivered
        or not user.active
    ):
        return
    tg_id = str(sender["id"])
    if kind == "login":
        identity = db.scalar(select(TelegramIdentity).where(TelegramIdentity.user_id == user.id))
        if not identity or identity.telegram_user_id != tg_id:
            return  # A forwarded start link never authenticates a different Telegram user.
        code = f"{secrets.randbelow(1000000):06d}"
        row.code_hash = otp_hash(row, code)
        row.delivered = True
        db.commit()
        try:
            transport.send(
                tg_id,
                "SMART STUDY CONTROL kirish kodi: "
                + code
                + "\n5 daqiqa amal qiladi. Kodni hech kimga bermang. Siz boshlamagan bo‘lsangiz, ishlatmang.",
            )
        except HTTPException:
            row = lock_challenge(db, row.id)
            row.delivered, row.code_hash = False, None
            db.commit()
            raise
    else:
        row.payload = {"telegram_user_id": tg_id, "chat_id": tg_id}
        row.delivered = True
        db.commit()
        transport.send(
            tg_id,
            "SMART STUDY CONTROL: bog‘lash so‘rovi qabul qilindi. Ilovaga qaytib hisob parolingiz bilan tasdiqlang. Bu xabarning o‘zi hisobni bog‘lamaydi.",
        )
