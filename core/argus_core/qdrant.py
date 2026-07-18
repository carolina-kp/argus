"""Async Qdrant wrapper for the `regulatory` collection."""
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models

from argus_core.config import settings

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=settings.qdrant_url)
    return _client


async def ensure_regulatory_collection() -> None:
    """Create the collection and payload indexes if missing (idempotent)."""
    client = get_client()
    name = settings.qdrant_regulatory_collection
    if not await client.collection_exists(name):
        await client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dim, distance=models.Distance.COSINE
            ),
        )
        for field in ("source", "jurisdiction", "ref"):
            await client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )


async def upsert_points(
    ids: list[str], vectors: list[list[float]], payloads: list[dict[str, Any]]
) -> None:
    id_list: list[int | str | UUID] = list(ids)
    await get_client().upsert(
        collection_name=settings.qdrant_regulatory_collection,
        points=models.Batch(ids=id_list, vectors=vectors, payloads=payloads),
    )


async def existing_content_hashes() -> dict[str, str]:
    """Map of point_id -> content_hash for every point currently in the collection.

    Used by ingestion to re-embed only chunks whose text changed.
    """
    client = get_client()
    name = settings.qdrant_regulatory_collection
    if not await client.collection_exists(name):
        return {}
    hashes: dict[str, str] = {}
    offset: Any = None
    while True:
        points, offset = await client.scroll(
            collection_name=name,
            limit=256,
            offset=offset,
            with_payload=["content_hash"],
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            if "content_hash" in payload:
                hashes[str(p.id)] = payload["content_hash"]
        if offset is None:
            break
    return hashes


async def search_regulatory(
    vector: list[float], top_k: int, jurisdiction: str | None = None
) -> list[tuple[float, dict[str, Any]]]:
    """Return (score, payload) pairs, best first."""
    query_filter = None
    if jurisdiction:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="jurisdiction", match=models.MatchValue(value=jurisdiction)
                )
            ]
        )
    result = await get_client().query_points(
        collection_name=settings.qdrant_regulatory_collection,
        query=vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [(p.score, dict(p.payload or {})) for p in result.points]
