import logging

logger = logging.getLogger("argus.worker")


def heartbeat() -> None:
    logger.info('{"job":"heartbeat","status":"alive"}')
