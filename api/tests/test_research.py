"""Research endpoint tests with mocked retrieval and LLM."""
from typing import Any

import pytest
from httpx import AsyncClient

from app.routers import research
from tests.conftest import auth_headers

MICA_HIT = (
    0.82,
    {
        "source": "mica",
        "document": "Regulation (EU) 2023/1114 (MiCA)",
        "ref": "Article 6",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114",
        "text": "Article 6 — Content and form of the crypto-asset white paper ...",
    },
)
FINMA_HIT = (
    0.61,
    {
        "source": "finma",
        "document": "FINMA ICO Guidelines (2018)",
        "ref": "3.1",
        "url": "https://www.finma.ch/...",
        "text": "3.1 Token categories ...",
    },
)


def _patch(
    monkeypatch: pytest.MonkeyPatch,
    hits: list[tuple[float, dict[str, Any]]],
    answer: str = (
        "White papers must contain issuer information [1]. "
        "FINMA distinguishes token types [2]."
    ),
) -> None:
    async def fake_search(vector: list[float], top_k: int, jurisdiction: str | None = None) -> Any:
        return hits

    async def fake_generate(system: str, user: str) -> str:
        return answer

    monkeypatch.setattr(research, "embed_query", lambda q: [0.0] * 384)
    monkeypatch.setattr(research, "search_regulatory", fake_search)
    monkeypatch.setattr(research, "generate", fake_generate)


async def test_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/research/ask", json={"question": "What is MiCA?"})
    assert resp.status_code == 401


async def test_refuses_below_cutoff(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, hits=[(0.12, MICA_HIT[1])])
    resp = await client.post(
        "/research/ask", json={"question": "best pizza in Zug?"}, headers=auth_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answered"] is False
    assert data["answer"] is None
    assert "does not cover" in data["message"]


async def test_answers_with_citations(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, hits=[MICA_HIT, FINMA_HIT])
    resp = await client.post(
        "/research/ask",
        json={"question": "What must a crypto-asset white paper contain?"},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answered"] is True
    assert "[1]" in data["answer"]
    cited = {c["n"]: c for c in data["citations"]}
    assert cited[1]["ref"] == "Article 6"
    assert cited[2]["ref"] == "3.1"
    assert cited[1]["url"].startswith("https://eur-lex.europa.eu/")


async def test_uncited_hits_are_excluded(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch, hits=[MICA_HIT, FINMA_HIT], answer="Only the first source matters [1].")
    resp = await client.post(
        "/research/ask", json={"question": "whitepaper content"}, headers=auth_headers()
    )
    data = resp.json()
    assert [c["n"] for c in data["citations"]] == [1]


async def test_query_is_logged(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, hits=[MICA_HIT])
    await client.post(
        "/research/ask", json={"question": "log me"}, headers=auth_headers()
    )
    # Fetch the log through a fresh session from the overridden dependency.
    from argus_core.db import get_session as real_dep
    from argus_core.models import RagQuery
    from sqlalchemy import select

    from app.main import app

    override = app.dependency_overrides[real_dep]
    agen = override()
    session = await agen.__anext__()
    rows = (await session.execute(select(RagQuery))).scalars().all()
    assert len(rows) == 1
    assert rows[0].question == "log me"
    assert rows[0].refused is False
    assert rows[0].retrieved[0]["ref"] == "Article 6"
    await agen.aclose()
