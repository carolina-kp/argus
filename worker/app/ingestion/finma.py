"""FINMA ingestion: ICO guidelines and stablecoin supplement PDFs from finma.ch.

Both documents use numbered sections ("2 Making an enquiry", "3.1 ..."), which
are the split boundaries. Extraction is validated by the caller printing a
sample of extracted text (scanned-image PDFs would yield garbage or nothing).
"""
import io
import re
from dataclasses import dataclass

import httpx
from pypdf import PdfReader

from app.ingestion.types import Chunk, split_oversized


@dataclass(frozen=True)
class FinmaDoc:
    title: str
    url: str


FINMA_DOCS = [
    FinmaDoc(
        title="FINMA Guidelines for enquiries regarding the regulatory framework for ICOs (2018)",
        url=(
            "https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/"
            "myfinma/1bewilligung/fintech/wegleitung-ico.pdf"
        ),
    ),
    FinmaDoc(
        title="FINMA Supplement to the ICO guidelines for enquiries regarding stable coins (2019)",
        url=(
            "https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/"
            "myfinma/1bewilligung/fintech/wegleitung-stable-coins.pdf"
        ),
    ),
]

# Numbered section heading at line start: "2 Making an enquiry", "3.1 Payment tokens"
_SECTION = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Z(«\"].{2,80})$")
_PAGE_NOISE = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")


def fetch_pdf(url: str) -> bytes:
    resp = httpx.get(url, timeout=120.0, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.content


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_finma(text: str, doc: FinmaDoc) -> list[Chunk]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    sections: list[tuple[str, str, list[str]]] = []  # (number, heading, body lines)
    current: tuple[str, str, list[str]] | None = None
    for ln in lines:
        if _PAGE_NOISE.match(ln):
            continue
        m = _SECTION.match(ln.strip())
        if m:
            if current:
                sections.append(current)
            current = (m.group(1), m.group(2).strip(), [])
        elif current:
            current[2].append(ln)
    if current:
        sections.append(current)

    chunks: list[Chunk] = []
    for number, heading, body_lines in sections:
        body = "\n".join(ln for ln in body_lines if ln.strip())
        if not body.strip():
            continue
        chunk = Chunk(
            source="finma",
            document=doc.title,
            ref=number,
            jurisdiction="CH",
            url=doc.url,
            text=f"{number} {heading}\n{body}",
        )
        chunks.extend(split_oversized(chunk))
    return chunks
