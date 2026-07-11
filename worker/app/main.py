import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs import (
    anomaly_scan,
    daily_brief,
    heartbeat,
    ingest_regulatory,
    market_snapshot,
    onchain_snapshot,
    tvl_snapshot,
)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("argus.worker")


def main() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(heartbeat, "interval", minutes=1, id="heartbeat")
    scheduler.add_job(market_snapshot, "interval", minutes=15, id="market_snapshot")
    scheduler.add_job(tvl_snapshot, "interval", hours=1, id="tvl_snapshot")
    scheduler.add_job(onchain_snapshot, "interval", hours=1, id="onchain_snapshot")
    scheduler.add_job(anomaly_scan, "interval", minutes=30, id="anomaly_scan")
    # Daily brief at 07:00 Europe/Zurich (CET/CEST).
    scheduler.add_job(
        daily_brief, "cron", hour=7, minute=0, timezone="Europe/Zurich", id="daily_brief"
    )
    # Weekly regulatory refresh (Mondays 05:00 UTC); manual: `python -m app.ingest`.
    scheduler.add_job(ingest_regulatory, "cron", day_of_week="mon", hour=5, id="ingest_regulatory")
    scheduler.start()
    logger.info('{"event":"worker_started"}')

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
