"""Embed chunks locally and batch-upsert them to Qdrant.

Only chunks whose text changed since the last ingestion are re-embedded:
each point stores a content_hash and unchanged chunks are skipped.
"""
import logging

from argus_core.embeddings import embed_passages
from argus_core.qdrant import (
    ensure_regulatory_collection,
    existing_content_hashes,
    upsert_points,
)

from app.ingestion.types import Chunk

logger = logging.getLogger("argus.worker")

BATCH = 64


async def embed_and_upsert(chunks: list[Chunk]) -> int:
    """Embed and upsert changed chunks. Returns the number embedded."""
    await ensure_regulatory_collection()
    existing = await existing_content_hashes()

    changed = [c for c in chunks if existing.get(c.point_id) != c.content_hash]
    skipped = len(chunks) - len(changed)
    if skipped:
        logger.info('{"ingest":"diff","unchanged":%d,"changed":%d}', skipped, len(changed))

    total = 0
    for i in range(0, len(changed), BATCH):
        batch = changed[i : i + BATCH]
        vectors = embed_passages([c.text for c in batch])
        await upsert_points(
            ids=[c.point_id for c in batch],
            vectors=vectors,
            payloads=[c.payload() for c in batch],
        )
        total += len(batch)
        logger.info('{"ingest":"upsert","done":%d,"total":%d}', total, len(changed))
    return total
