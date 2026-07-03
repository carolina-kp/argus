"""Regulatory corpus ingestion pipeline. Manual trigger: `python -m app.ingest`.

Also runs weekly via APScheduler (see app.jobs.ingest_regulatory).
"""
import asyncio
import logging

from app.ingestion.embed import embed_and_upsert
from app.ingestion.finma import FINMA_DOCS, extract_text, fetch_pdf, parse_finma
from app.ingestion.mica import EXPECTED_ARTICLES, fetch_mica_html, parse_mica
from app.ingestion.types import Chunk
from app.ingestion.whitepapers import (
    WHITEPAPERS,
    fetch,
    parse_html_whitepaper,
    parse_pdf_whitepaper,
)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("argus.worker")


async def run_ingestion() -> int:
    chunks: list[Chunk] = []

    # 1. MiCA
    mica_chunks = parse_mica(fetch_mica_html())
    articles = {c.ref for c in mica_chunks}
    logger.info('{"ingest":"mica","articles":%d,"chunks":%d}', len(articles), len(mica_chunks))
    if len(articles) != EXPECTED_ARTICLES:
        logger.warning(
            '{"ingest":"mica","warn":"article count %d != expected %d"}',
            len(articles), EXPECTED_ARTICLES,
        )
    chunks.extend(mica_chunks)

    # 2. FINMA — log an extraction sample so a scan-only PDF is caught by eye.
    for doc in FINMA_DOCS:
        text = extract_text(fetch_pdf(doc.url))
        sample = " ".join(text.split())[:300]
        logger.info('{"ingest":"finma","doc":"%s","sample":"%s"}', doc.title[:40], sample)
        doc_chunks = parse_finma(text, doc)
        logger.info('{"ingest":"finma","doc":"%s","chunks":%d}', doc.title[:40], len(doc_chunks))
        chunks.extend(doc_chunks)

    # 3. Whitepapers
    for wp in WHITEPAPERS:
        try:
            raw = fetch(wp.url)
        except Exception as exc:  # noqa: BLE001 - one bad source must not sink the run
            logger.warning('{"ingest":"whitepaper","symbol":"%s","error":"%s"}', wp.symbol, exc)
            continue
        if wp.kind == "pdf":
            wp_chunks = parse_pdf_whitepaper(raw, wp)
        else:
            wp_chunks = parse_html_whitepaper(raw.decode("utf-8", errors="replace"), wp)
        logger.info('{"ingest":"whitepaper","symbol":"%s","chunks":%d}', wp.symbol, len(wp_chunks))
        chunks.extend(wp_chunks)

    # 4. Embed + upsert
    total = await embed_and_upsert(chunks)
    logger.info('{"ingest":"done","chunks":%d}', total)
    return total


if __name__ == "__main__":
    asyncio.run(run_ingestion())
