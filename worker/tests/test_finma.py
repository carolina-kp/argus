"""FINMA parser tests against the real finma.ch PDFs (committed fixtures)."""
from pathlib import Path

import pytest

from app.ingestion.finma import FINMA_DOCS, extract_text, parse_finma
from app.ingestion.types import Chunk

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def ico_chunks() -> list[Chunk]:
    text = extract_text((FIXTURES / "finma_ico.pdf").read_bytes())
    return parse_finma(text, FINMA_DOCS[0])


@pytest.fixture(scope="module")
def stablecoin_chunks() -> list[Chunk]:
    text = extract_text((FIXTURES / "finma_stablecoin.pdf").read_bytes())
    return parse_finma(text, FINMA_DOCS[1])


def test_extraction_is_real_text_not_scan() -> None:
    text = extract_text((FIXTURES / "finma_ico.pdf").read_bytes())
    # A scanned-image PDF yields (near-)empty text; the real one is ~18k chars.
    assert len(text) > 10_000
    assert "FINMA" in text and "token" in text.lower()


def test_ico_guidelines_split_into_sections(ico_chunks: list[Chunk]) -> None:
    assert len(ico_chunks) >= 5
    refs = {c.ref for c in ico_chunks}
    assert "2" in refs  # "2 Making an enquiry"
    assert any(r.startswith("3.") for r in refs)  # subsections exist


def test_token_categories_section_present(ico_chunks: list[Chunk]) -> None:
    # FINMA's token taxonomy (payment/utility/asset) lives in section 3.1.
    taxonomy = [c for c in ico_chunks if "payment token" in c.text.lower()]
    assert taxonomy, "expected FINMA token taxonomy content"


def test_metadata_discipline(ico_chunks: list[Chunk], stablecoin_chunks: list[Chunk]) -> None:
    for c in ico_chunks + stablecoin_chunks:
        assert c.source == "finma"
        assert c.jurisdiction == "CH"
        assert c.url.startswith("https://www.finma.ch/")
        assert c.ref[0].isdigit()
        assert c.text.strip()


def test_stablecoin_supplement_parses(stablecoin_chunks: list[Chunk]) -> None:
    assert len(stablecoin_chunks) >= 3
    assert any("stable coin" in c.text.lower() for c in stablecoin_chunks)
