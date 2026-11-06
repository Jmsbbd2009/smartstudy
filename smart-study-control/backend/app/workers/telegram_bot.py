"""Opt-in Telegram worker. Polling never deletes someone else's existing webhook."""

import argparse
import time
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.core.config import settings
from app.integrations.telegram import transport, process_update
from app.models.entities import TelegramIdentity, TelegramDelivery, Notification, LocationShare, User, now
from app.api.location import erase


def deliveries():
    # Only linked staff who explicitly enable Telegram copies are eligible.
    with SessionLocal() as db:
        messages = list(
            db.execute(
                select(Notification, TelegramIdentity)
                .join(TelegramIdentity, TelegramIdentity.user_id == Notification.user_id)
                .join(User, User.id == Notification.user_id)
                .where(
                    TelegramIdentity.notifications_enabled.is_(True),
                    User.active.is_(True),
                    User.role.in_(["TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"]),
                    Notification.created_at >= TelegramIdentity.updated_at,
                )
                .order_by(Notification.created_at.desc())
                .limit(100)
            )
        )
        for note, identity in messages:
            row = db.scalar(select(TelegramDelivery).where(TelegramDelivery.notification_id == note.id))
            if not row:
                try:
                    with db.begin_nested():
                        row = TelegramDelivery(notification_id=note.id)
                        db.add(row)
                        db.flush()
                except IntegrityError:
                    row = db.scalar(
                        select(TelegramDelivery).where(TelegramDelivery.notification_id == note.id)
                    )
            if row.status in ("SENT", "FAILED") or row.attempts >= 3:
                continue
            # Lease protects against concurrent worker sends. Ambiguous transport failure
            # can produce one duplicate message; never claim exactly-once external delivery.
            from datetime import timedelta

            claim = db.execute(
                update(TelegramDelivery)
                .where(
                    TelegramDelivery.id == row.id,
                    (TelegramDelivery.status == "PENDING")
                    | (
                        (TelegramDelivery.status == "SENDING")
                        & (TelegramDelivery.updated_at < now() - timedelta(minutes=2))
                    ),
                )
                .values(status="SENDING", attempts=TelegramDelivery.attempts + 1, updated_at=now())
            )
            db.commit()
            if claim.rowcount != 1:
                continue
            try:
                transport.send(identity.chat_id, "SMART STUDY CONTROL\n" + note.title + "\n" + note.body)
                row.status = "SENT"
            except Exception:
                db.refresh(row)
                row.status = "FAILED" if row.attempts >= 3 else "PENDING"
            db.commit()
        # Latest coordinates have no history and are removed after expiry.
        for share in db.scalars(
            select(LocationShare).where(LocationShare.status == "ACTIVE", LocationShare.expires_at <= now())
        ):
            erase(share, "EXPIRED")
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings.validate()
    if transport.call("getWebhookInfo").get("url"):
        raise SystemExit(
            "An existing Telegram webhook is active. Configure this project webhook or remove it in an attended operation before polling."
        )
    offset = None
    while True:
        updates = transport.call(
            "getUpdates",
            {"timeout": 0 if args.once else 25, "offset": offset, "allowed_updates": ["message"]},
        )
        for item in updates:
            with SessionLocal() as db:
                try:
                    process_update(db, item)
                except Exception:
                    db.rollback()  # No request URLs, OTPs or tokens in logs.
            offset = item["update_id"] + 1
        deliveries()
        if args.once:
            return
        time.sleep(1)


if __name__ == "__main__":
    main()
