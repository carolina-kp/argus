"""Generate today's daily brief on demand instead of waiting for the 07:00 cron.

Same code path as the scheduled job (build, store, email-or-skip); upserts the
brief for the current date. Run with `python -m app.run_brief`.
"""
import asyncio
import logging

from app.brief import run_daily_brief

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')

if __name__ == "__main__":
    asyncio.run(run_daily_brief())
