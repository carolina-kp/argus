import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs import heartbeat

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("argus.worker")


def main() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(heartbeat, "interval", minutes=1, id="heartbeat")
    scheduler.start()
    logger.info('{"event":"worker_started"}')

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
