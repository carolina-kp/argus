"""MiCA ingestion: Regulation (EU) 2023/1114 from EUR-Lex.

The official HTML wraps each article in `<div class="eli-subdivision" id="art_N">`
with the number in `p.oj-ti-art` and the title in `p.oj-sti-art`, which makes
article boundaries the natural, lossless chunking unit.
"""
import re

import httpx
from bs4 import BeautifulSoup, Tag

from app.ingestion.types import Chunk, split_oversized

MICA_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114"
MICA_TITLE = "Regulation (EU) 2023/1114 (MiCA)"
EXPECTED_ARTICLES = 149

_ART_ID = re.compile(r"^art_(\d+)$")
_WS = re.compile(r"[\s   ]+")


def fetch_mica_html() -> str:
    resp = httpx.get(MICA_URL, timeout=120.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _clean(text: str) -> str:
    return _WS.sub(" ", text).strip()


def parse_mica(html: str) -> list[Chunk]:
    soup = BeautifulSoup(html, "html.parser")
    chunks: list[Chunk] = []
    for div in soup.find_all("div", class_="eli-subdivision"):
        if not isinstance(div, Tag):
            continue
        div_id = div.get("id")
        if not isinstance(div_id, str) or not _ART_ID.match(div_id):
            continue
        num_el = div.find("p", class_="oj-ti-art")
        title_el = div.find("p", class_="oj-sti-art")
        if num_el is None:
            continue
        article_no = _clean(num_el.get_text())  # "Article N"
        title = _clean(title_el.get_text()) if title_el else ""
        # Body: paragraph-level text, excluding the two title lines.
        lines: list[str] = []
        for p in div.find_all("p"):
            if not isinstance(p, Tag):
                continue
            raw_cls = p.get("class")
            classes = raw_cls if isinstance(raw_cls, list) else []
            if "oj-ti-art" in classes or "oj-sti-art" in classes:
                continue
            text = _clean(p.get_text())
            if text:
                lines.append(text)
        body = "\n".join(lines)
        chunk = Chunk(
            source="mica",
            document=MICA_TITLE,
            ref=article_no,
            jurisdiction="EU",
            url=MICA_URL,
            text=f"{article_no} — {title}\n{body}" if title else f"{article_no}\n{body}",
        )
        chunks.extend(split_oversized(chunk))
    return chunks
