"""Bounded opt-in daily practice worker; run with --once for an attended single tick."""

import argparse
import logging
import time
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import AutomationSetting, User
from app.services.autopilot import run_daily

logger = logging.getLogger("study.autopilot")


def tick():
    from app.models.entities import LocationShare, now
    from app.api.location import erase

    with SessionLocal.begin() as cleanup_db:
        for share in cleanup_db.scalars(
            select(LocationShare).where(LocationShare.status == "ACTIVE", LocationShare.expires_at <= now())
        ):
            erase(share, "EXPIRED")
    with SessionLocal() as db:
        pending = [
            (s.child_id, s.guardian_id)
            for s in db.scalars(
                select(AutomationSetting).where(
                    AutomationSetting.enabled.is_(True), AutomationSetting.auto_practice.is_(True)
                )
            )
        ]
    for child, guardian_id in pending:
        with SessionLocal() as db:
            try:
                run_daily(db, db.get(User, guardian_id), child)
            except Exception as exc:
                db.rollback()
                logger.info("Daily practice skipped (%s)", type(exc).__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings.validate()
    logging.basicConfig(level=logging.INFO)
    while True:
        tick()
        if args.once:
            return
        time.sleep(300)


if __name__ == "__main__":
    main()
