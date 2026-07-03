"""Whitepaper ingestion: BTC, ETH, plus watchlist protocols (AAVE, UNI, LINK).

PDFs split on numbered headings ("2. Transactions", "3.1 ..."); the ETH
whitepaper is HTML and splits on h2/h3 headings.
"""
import io
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag
from pypdf import PdfReader

from app.ingestion.types import Chunk, split_oversized


@dataclass(frozen=True)
class Whitepaper:
    symbol: str
    title: str
    url: str
    kind: str  # pdf | html


WHITEPAPERS = [
    Whitepaper("BTC", "Bitcoin: A Peer-to-Peer Electronic Cash System",
               "https://bitcoin.org/bitcoin.pdf", "pdf"),
    Whitepaper("ETH", "Ethereum Whitepaper",
               "https://ethereum.org/en/whitepaper/", "html"),
    Whitepaper("AAVE", "Aave V3 Technical Paper",
               "https://raw.githubusercontent.com/aave/aave-v3-core/master/techpaper/"
               "Aave_V3_Technical_Paper.pdf", "pdf"),
    Whitepaper("UNI", "Uniswap v3 Core",
               "https://app.uniswap.org/whitepaper-v3.pdf", "pdf"),
    Whitepaper("LINK", "Chainlink 2.0 Whitepaper",
               "https://research.chain.link/whitepaper-v2.pdf", "pdf"),
]

# "2. Transactions" / "3.1 Concentrated Liquidity" / "10 Privacy" at line start.
_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z].{2,70})$")


def fetch(url: str) -> bytes:
    resp = httpx.get(url, timeout=180.0, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.content


def parse_pdf_whitepaper(pdf_bytes: bytes, wp: Whitepaper) -> list[Chunk]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    sections: list[tuple[str, list[str]]] = [("Introduction (preamble)", [])]
    for ln in text.splitlines():
        m = _HEADING.match(ln.strip())
        if m:
            sections.append((f"{m.group(1)} {m.group(2).strip()}", []))
        else:
            sections[-1][1].append(ln)
    return _to_chunks(sections, wp)


def parse_html_whitepaper(html: str, wp: Whitepaper) -> list[Chunk]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    root: Tag | BeautifulSoup = main if isinstance(main, Tag) else soup
    sections: list[tuple[str, list[str]]] = [("Introduction (preamble)", [])]
    for el in root.find_all(["h2", "h3", "p", "li"]):
        if not isinstance(el, Tag):
            continue
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name in ("h2", "h3"):
            sections.append((text, []))
        else:
            sections[-1][1].append(text)
    return _to_chunks(sections, wp)


def _to_chunks(sections: list[tuple[str, list[str]]], wp: Whitepaper) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, body_lines in sections:
        body = "\n".join(ln for ln in body_lines if ln.strip())
        if len(body.strip()) < 80:  # skip empty/near-empty sections (TOC artifacts)
            continue
        chunk = Chunk(
            source="whitepaper",
            document=f"{wp.title} ({wp.symbol})",
            ref=heading,
            jurisdiction="GLOBAL",
            url=wp.url,
            text=f"{heading}\n{body}",
        )
        chunks.extend(split_oversized(chunk))
    return chunks
