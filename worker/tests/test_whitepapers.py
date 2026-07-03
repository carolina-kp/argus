"""Whitepaper parser tests against the real Bitcoin whitepaper (committed fixture)."""
from pathlib import Path

import pytest

from app.ingestion.types import MAX_CHUNK_CHARS, Chunk
from app.ingestion.whitepapers import WHITEPAPERS, parse_pdf_whitepaper

FIXTURES = Path(__file__).parent / "fixtures"
BTC = WHITEPAPERS[0]


@pytest.fixture(scope="module")
def btc_chunks() -> list[Chunk]:
    return parse_pdf_whitepaper((FIXTURES / "btc.pdf").read_bytes(), BTC)


def test_btc_splits_by_numbered_headings(btc_chunks: list[Chunk]) -> None:
    refs = [c.ref for c in btc_chunks]
    assert any("Introduction" in r for r in refs)
    assert any("Transactions" in r for r in refs)
    assert any("Proof-of-Work" in r for r in refs)


def test_btc_metadata(btc_chunks: list[Chunk]) -> None:
    for c in btc_chunks:
        assert c.source == "whitepaper"
        assert c.jurisdiction == "GLOBAL"
        assert c.document.endswith("(BTC)")
        assert c.url == "https://bitcoin.org/bitcoin.pdf"


def test_chunks_respect_size_budget(btc_chunks: list[Chunk]) -> None:
    for c in btc_chunks:
        assert len(c.text) <= MAX_CHUNK_CHARS + 200  # small tolerance for one long paragraph
