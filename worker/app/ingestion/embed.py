"""Embed chunks locally and batch-upsert them to Qdrant."""
import logging

from argus_core.embeddings import embed_passages
from argus_core.qdrant import ensure_regulatory_collection, upsert_points

from app.ingestion.types import Chunk

logger = logging.getLogger("argus.worker")

BATCH = 64


async def embed_and_upsert(chunks: list[Chunk]) -> int:
    await ensure_regulatory_collection()
    total = 0
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        vectors = embed_passages([c.text for c in batch])
        await upsert_points(
            ids=[c.point_id for c in batch],
            vectors=vectors,
            payloads=[c.payload() for c in batch],
        )
        total += len(batch)
        logger.info('{"ingest":"upsert","done":%d,"total":%d}', total, len(chunks))
    return total
