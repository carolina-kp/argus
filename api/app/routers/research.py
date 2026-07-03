"""Regulatory research chat: retrieval over the `regulatory` collection with
mandatory inline citations and an honest refusal path below the score cutoff.
"""
import asyncio
import logging
import re
import time
from typing import Any

from argus_core.config import settings
from argus_core.db import get_session
from argus_core.embeddings import embed_query
from argus_core.llm import LLMError, generate
from argus_core.models import RagQuery
from argus_core.prompts import load_prompt
from argus_core.qdrant import search_regulatory
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_token
from app.schemas import Citation, ResearchAnswer, ResearchAsk

router = APIRouter(prefix="/research", tags=["research"], dependencies=[Depends(require_token)])
logger = logging.getLogger("argus.api")

_CITE = re.compile(r"\[(\d+)\]")

NOT_COVERED = (
    "The regulatory corpus does not cover this question with enough confidence "
    "to answer. Try rephrasing, or ask about MiCA, FINMA guidance, or the "
    "indexed protocol whitepapers."
)


async def _rewrite(question: str) -> str | None:
    """Best-effort query rewrite; on any failure retrieval uses the raw question."""
    try:
        rewritten = await generate(load_prompt("rag_rewrite_v1"), question)
        return rewritten.strip().strip('"') or None
    except LLMError:
        return None


def _context_block(hits: list[tuple[float, dict[str, Any]]]) -> str:
    parts = []
    for i, (_score, payload) in enumerate(hits, start=1):
        parts.append(
            f"[{i}] {payload['document']} — {payload['ref']}\n{payload['text']}"
        )
    return "\n\n".join(parts)


@router.post("/ask", response_model=ResearchAnswer)
async def ask(
    body: ResearchAsk,
    session: AsyncSession = Depends(get_session),
) -> ResearchAnswer:
    question = body.question.strip()
    if not question:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "question is empty")
    started = time.monotonic()

    rewritten = await _rewrite(question)
    vector = await asyncio.to_thread(embed_query, rewritten or question)
    hits = await search_regulatory(vector, settings.rag_top_k, body.jurisdiction)
    max_score = max((s for s, _ in hits), default=0.0)

    retrieved_log = [
        {"score": round(s, 4), "document": p["document"], "ref": p["ref"], "url": p["url"]}
        for s, p in hits
    ]

    if max_score < settings.rag_score_cutoff:
        await _log(session, question, rewritten, body.jurisdiction, retrieved_log,
                   None, max_score, refused=True, started=started)
        return ResearchAnswer(answered=False, max_score=max_score, message=NOT_COVERED)

    user_prompt = (
        f"Context excerpts:\n\n{_context_block(hits)}\n\n"
        f"Question: {question}\n\n"
        "Answer using ONLY the excerpts above, with inline citations [n]."
    )
    try:
        answer = await generate(load_prompt("rag_answer_v1"), user_prompt)
    except LLMError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"LLM unavailable: {exc}") from exc

    cited = {int(n) for n in _CITE.findall(answer) if 1 <= int(n) <= len(hits)}
    citations = [
        Citation(n=i, document=p["document"], ref=p["ref"], url=p["url"], score=round(s, 4))
        for i, (s, p) in enumerate(hits, start=1)
        if i in cited
    ]

    await _log(session, question, rewritten, body.jurisdiction, retrieved_log,
               answer, max_score, refused=False, started=started)
    return ResearchAnswer(answered=True, answer=answer, citations=citations, max_score=max_score)


async def _log(
    session: AsyncSession,
    question: str,
    rewritten: str | None,
    jurisdiction: str | None,
    retrieved: list[dict[str, Any]],
    answer: str | None,
    max_score: float,
    refused: bool,
    started: float,
) -> None:
    session.add(
        RagQuery(
            question=question,
            rewritten_query=rewritten,
            jurisdiction=jurisdiction,
            retrieved=retrieved,
            answer=answer,
            max_score=max_score,
            refused=refused,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    )
    await session.commit()
