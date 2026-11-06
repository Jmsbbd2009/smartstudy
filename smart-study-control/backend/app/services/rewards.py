from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select, update, func
from app.models.entities import Wallet, RewardTransaction, UnlockSession, now


def locked_wallet(db, child):
    # A real write lock also serializes SQLite fallback tests; PostgreSQL locks this wallet row.
    result = db.execute(update(Wallet).where(Wallet.student_id == child).values(updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "Wallet not initialized")
    return db.scalar(
        select(Wallet).where(Wallet.student_id == child).execution_options(populate_existing=True)
    )


def credit(db, child, origin, amount, reference):
    wallet = locked_wallet(db, child)
    existing = db.scalar(select(RewardTransaction).where(RewardTransaction.origin == origin))
    if existing:
        return existing
    paid = min(wallet.debt, amount)
    wallet.debt -= paid
    wallet.available += amount - paid
    row = RewardTransaction(student_id=child, origin=origin, delta=amount, kind="EARN", reference=reference)
    db.add(row)
    db.flush()
    return row


def revoke(db, child, assignment):
    wallet = locked_wallet(db, child)
    earned = db.scalar(
        select(RewardTransaction).where(RewardTransaction.origin == "assignment:" + assignment)
    )
    if not earned:
        return
    origin = "revoke:" + assignment
    if db.scalar(select(RewardTransaction.id).where(RewardTransaction.origin == origin)):
        return
    debit = min(wallet.available, earned.delta)
    wallet.available -= debit
    wallet.debt += earned.delta - debit
    db.add(
        RewardTransaction(
            student_id=child, origin=origin, delta=-earned.delta, kind="REVOKE", reference=assignment
        )
    )


def refund(db, session):
    wallet = locked_wallet(db, session.student_id)
    origin = "refund:" + session.id
    if db.scalar(select(RewardTransaction.id).where(RewardTransaction.origin == origin)):
        return
    wallet.available += session.minutes
    session.status = "FAILED"
    db.add(
        RewardTransaction(
            student_id=session.student_id,
            origin=origin,
            delta=session.minutes,
            kind="REFUND",
            reference=session.id,
        )
    )


def settle_stale(db, child):
    locked_wallet(db, child)
    for session in db.scalars(
        select(UnlockSession)
        .where(UnlockSession.student_id == child, UnlockSession.status.in_(["PENDING", "ACTIVE"]))
        .execution_options(populate_existing=True)
    ):
        if session.expires_at <= now():
            if session.status == "PENDING":
                refund(db, session)
            else:
                session.status = "EXPIRED"


def reserve(db, child, body, key):
    wallet = locked_wallet(db, child)
    existing = db.scalar(
        select(UnlockSession).where(UnlockSession.student_id == child, UnlockSession.idempotency_key == key)
    )
    if existing:
        if (existing.device_id, existing.package, existing.minutes) != (
            body.device_id,
            body.package,
            body.minutes,
        ):
            raise HTTPException(409, "Idempotency key reused with different request")
        return existing
    settle_stale(db, child)
    if db.scalar(
        select(UnlockSession.id)
        .where(UnlockSession.student_id == child, UnlockSession.status.in_(["PENDING", "ACTIVE"]))
        .execution_options(populate_existing=True)
    ):
        raise HTTPException(409, "A reward access session is already open")
    day = now().replace(hour=0, minute=0, second=0, microsecond=0)
    week = day - timedelta(days=day.weekday())

    def used(since):
        return db.scalar(
            select(func.coalesce(func.sum(UnlockSession.minutes), 0)).where(
                UnlockSession.student_id == child,
                UnlockSession.created_at >= since,
                UnlockSession.status != "FAILED",
            )
        )

    if used(day) + body.minutes > wallet.daily_max or used(week) + body.minutes > wallet.weekly_max:
        raise HTTPException(409, "Entertainment budget reached")
    if wallet.available < body.minutes or wallet.debt > 0:
        raise HTTPException(409, "Insufficient available minutes")
    wallet.available -= body.minutes
    row = UnlockSession(
        student_id=child,
        device_id=body.device_id,
        package=body.package,
        minutes=body.minutes,
        idempotency_key=key,
        expires_at=now() + timedelta(seconds=90),
    )
    db.add(row)
    db.flush()
    db.add(
        RewardTransaction(
            student_id=child, origin="redeem:" + row.id, delta=-body.minutes, kind="SPEND", reference=row.id
        )
    )
    return row
