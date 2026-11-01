"""Run manually or as a single scheduled process; no secret is logged."""

import argparse
import logging
import time
from backend.db import SessionLocal
from backend.services.football import refresh

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronize football results and notify followers."
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=900)
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("Minimum interval is 60 seconds.")
    while True:
        try:
            with SessionLocal() as db:
                report = refresh(db)
                db.commit()
                print(report, flush=True)
        except Exception:
            logging.exception("Sync failed. Existing data is retained.")
        if args.once:
            break
        time.sleep(args.interval)
