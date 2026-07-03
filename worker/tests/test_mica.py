"""MiCA parser tests against the real EUR-Lex HTML (committed fixture).

Fixture: official HTML of Regulation (EU) 2023/1114, retrieved 2026-07-03.
"""
import gzip
from pathlib import Path

import pytest

from app.ingestion.mica import EXPECTED_ARTICLES, parse_mica
from app.ingestion.types import Chunk

FIXTURE = Path(__file__).parent / "fixtures" / "mica.html.gz"


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    html = gzip.decompress(FIXTURE.read_bytes()).decode("utf-8")
    return parse_mica(html)


def _article(chunks: list[Chunk], ref: str) -> list[Chunk]:
    return [c for c in chunks if c.ref == ref]


def test_article_count_matches_known_total(chunks: list[Chunk]) -> None:
    articles = {c.ref for c in chunks}
    assert len(articles) == EXPECTED_ARTICLES  # MiCA has exactly 149 articles


def test_all_chunks_have_metadata(chunks: list[Chunk]) -> None:
    for c in chunks:
        assert c.source == "mica"
        assert c.jurisdiction == "EU"
        assert c.ref.startswith("Article ")
        assert c.url.startswith("https://eur-lex.europa.eu/")
        assert c.text.strip()


def test_article_6_is_whitepaper_content(chunks: list[Chunk]) -> None:
    parts = _article(chunks, "Article 6")
    assert parts, "Article 6 missing"
    head = parts[0].text
    assert "Content and form of the crypto-asset white paper" in head
    assert "crypto-asset white paper shall contain" in head


def test_article_4_is_offers_to_public(chunks: list[Chunk]) -> None:
    parts = _article(chunks, "Article 4")
    assert parts, "Article 4 missing"
    expected = "Offers to the public of crypto-assets other than asset-referenced tokens"
    assert expected in parts[0].text


def test_article_36_is_art_authorisation(chunks: list[Chunk]) -> None:
    parts = _article(chunks, "Article 36")
    assert parts, "Article 36 missing"
    assert "asset-referenced token" in parts[0].text.lower()


def test_long_articles_split_but_keep_ref(chunks: list[Chunk]) -> None:
    multi = [c for c in chunks if c.part > 0]
    assert multi, "expected at least one long article to be split"
    for c in multi:
        assert c.ref.startswith("Article ")


def test_point_ids_are_unique(chunks: list[Chunk]) -> None:
    ids = [c.point_id for c in chunks]
    assert len(ids) == len(set(ids))
