"""Shared chunk shape for all regulatory/whitepaper ingestion."""
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Rough character budget per chunk (~600 tokens for bge-small's 512-token window,
# plus headroom: oversized text is split at paragraph boundaries).
MAX_CHUNK_CHARS = 2400


@dataclass
class Chunk:
    source: str  # mica | finma | whitepaper
    document: str  # human-readable document title
    ref: str  # "Article 6", "3.1", or heading text
    jurisdiction: str  # EU | CH | GLOBAL
    url: str
    text: str
    part: int = 0  # sub-chunk index when one ref is split
    retrieval_date: str = field(
        default_factory=lambda: datetime.now(UTC).date().isoformat()
    )

    @property
    def point_id(self) -> str:
        """Deterministic Qdrant ID so re-ingestion is idempotent (UUID format)."""
        raw = f"{self.source}|{self.document}|{self.ref}|{self.part}"
        h = hashlib.sha256(raw.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "document": self.document,
            "ref": self.ref,
            "jurisdiction": self.jurisdiction,
            "url": self.url,
            "text": self.text,
            "part": self.part,
            "retrieval_date": self.retrieval_date,
        }


def split_oversized(chunk: Chunk, max_chars: int = MAX_CHUNK_CHARS) -> list[Chunk]:
    """Split a too-long chunk at paragraph boundaries, keeping ref metadata."""
    if len(chunk.text) <= max_chars:
        return [chunk]
    paragraphs = [p for p in chunk.text.split("\n") if p.strip()]
    parts: list[str] = []
    buf = ""
    for p in paragraphs:
        if buf and len(buf) + len(p) + 1 > max_chars:
            parts.append(buf)
            buf = p
        else:
            buf = f"{buf}\n{p}" if buf else p
    if buf:
        parts.append(buf)
    return [
        Chunk(
            source=chunk.source,
            document=chunk.document,
            ref=chunk.ref,
            jurisdiction=chunk.jurisdiction,
            url=chunk.url,
            text=part,
            part=i,
            retrieval_date=chunk.retrieval_date,
        )
        for i, part in enumerate(parts)
    ]
