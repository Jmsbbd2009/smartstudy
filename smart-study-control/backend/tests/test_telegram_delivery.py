from datetime import timedelta
from sqlalchemy import select
from app.models.entities import TelegramIdentity, TelegramDelivery, Notification, User, now
from app.workers import telegram_bot


def test_only_active_opted_in_staff_receive_new_notifications_once(people, monkeypatch):
    c, f, p = people
    sent = []
    monkeypatch.setattr(telegram_bot, "SessionLocal", f)
    monkeypatch.setattr(telegram_bot.transport, "send", lambda chat, text: sent.append((chat, text)))
    with f.begin() as db:
        db.add(
            TelegramIdentity(
                user_id=p["teacher3"]["id"],
                telegram_user_id="100",
                chat_id="100",
                notifications_enabled=True,
                updated_at=now() - timedelta(minutes=1),
            )
        )
        db.add(
            TelegramIdentity(
                user_id=p["teacher4"]["id"],
                telegram_user_id="200",
                chat_id="200",
                notifications_enabled=True,
                updated_at=now() - timedelta(minutes=1),
            )
        )
        db.get(User, p["teacher4"]["id"]).active = False
        db.add(Notification(user_id=p["teacher3"]["id"], title="New lesson", body="Prepare lesson"))
        db.add(
            Notification(
                user_id=p["teacher3"]["id"],
                title="Old lesson",
                body="Old",
                created_at=now() - timedelta(days=1),
            )
        )
        db.add(Notification(user_id=p["teacher4"]["id"], title="Disabled user", body="Hidden"))
        db.add(Notification(user_id=p["super_admin5"]["id"], title="No Telegram opt in", body="Hidden"))
    telegram_bot.deliveries()
    telegram_bot.deliveries()
    assert len(sent) == 1 and sent[0][0] == "100" and "New lesson" in sent[0][1]
    with f() as db:
        assert db.scalar(select(TelegramDelivery)).status == "SENT"


def test_failed_external_delivery_has_three_attempt_cap(people, monkeypatch):
    c, f, p = people
    calls = []
    monkeypatch.setattr(telegram_bot, "SessionLocal", f)

    def fail(*args):
        calls.append(1)
        raise RuntimeError("Transport unavailable")

    monkeypatch.setattr(telegram_bot.transport, "send", fail)
    with f.begin() as db:
        db.add(
            TelegramIdentity(
                user_id=p["teacher3"]["id"],
                telegram_user_id="100",
                chat_id="100",
                notifications_enabled=True,
                updated_at=now() - timedelta(minutes=1),
            )
        )
        db.add(Notification(user_id=p["teacher3"]["id"], title="New lesson", body="Prepare lesson"))
    for _ in range(4):
        telegram_bot.deliveries()
    assert len(calls) == 3
    with f() as db:
        assert db.scalar(select(TelegramDelivery)).status == "FAILED"
