import pytest

from app.ingestion import embed as embed_mod
from app.ingestion.types import Chunk


def _chunk(ref: str, text: str) -> Chunk:
    return Chunk(
        source="mica", document="MiCA", ref=ref, jurisdiction="EU",
        url="https://example.eu", text=text,
    )


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Patch Qdrant + embeddings; capture the point_ids actually upserted."""
    upserted: list[list[str]] = []

    async def fake_ensure() -> None:
        return None

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.1] for _ in texts]

    async def fake_upsert(ids: list[str], vectors: list[list[float]], payloads: list[dict]) -> None:
        upserted.append(list(ids))

    monkeypatch.setattr(embed_mod, "ensure_regulatory_collection", fake_ensure)
    monkeypatch.setattr(embed_mod, "embed_passages", fake_embed)
    monkeypatch.setattr(embed_mod, "upsert_points", fake_upsert)
    return upserted


@pytest.mark.asyncio
async def test_embeds_all_when_collection_empty(
    captured: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_existing() -> dict[str, str]:
        return {}

    monkeypatch.setattr(embed_mod, "existing_content_hashes", no_existing)
    chunks = [_chunk("Article 1", "alpha"), _chunk("Article 2", "beta")]
    assert await embed_mod.embed_and_upsert(chunks) == 2


@pytest.mark.asyncio
async def test_skips_unchanged(
    captured: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    chunks = [_chunk("Article 1", "alpha"), _chunk("Article 2", "beta")]
    existing = {c.point_id: c.content_hash for c in chunks}

    async def all_existing() -> dict[str, str]:
        return existing

    monkeypatch.setattr(embed_mod, "existing_content_hashes", all_existing)
    assert await embed_mod.embed_and_upsert(chunks) == 0
    assert captured == []  # nothing upserted


@pytest.mark.asyncio
async def test_reembeds_only_changed(
    captured: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    old = [_chunk("Article 1", "alpha"), _chunk("Article 2", "beta")]
    existing = {c.point_id: c.content_hash for c in old}

    async def some_existing() -> dict[str, str]:
        return existing

    monkeypatch.setattr(embed_mod, "existing_content_hashes", some_existing)
    # Article 2 text changed; Article 1 unchanged.
    new = [_chunk("Article 1", "alpha"), _chunk("Article 2", "beta v2")]
    assert await embed_mod.embed_and_upsert(new) == 1
    assert captured == [[new[1].point_id]]
