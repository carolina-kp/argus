"""Daily brief assembly: pull structured data from Postgres, run one
regulatory retrieval pass, generate Markdown via the LLM provider, store,
and email. Scheduled 07:00 CET; see app.jobs.daily_brief.
"""
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from argus_core.db import SessionLocal
from argus_core.email import EmailNotConfigured, send_email
from argus_core.embeddings import embed_query
from argus_core.llm import LLMError, generate
from argus_core.models import Brief, PriceSnapshot, TvlSnapshot, UnlockEvent, Watchlist
from argus_core.prompts import load_prompt
from argus_core.qdrant import search_regulatory
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("argus.worker")

_LOOKBACK = timedelta(hours=26)  # enough to find a ~24h-ago snapshot


def _pct(latest: float, prior: float) -> float | None:
    return round((latest - prior) / prior * 100, 2) if prior else None


async def _movers(session: AsyncSession, assets: list[Watchlist]) -> list[dict[str, Any]]:
    since = datetime.now(tz=UTC) - _LOOKBACK
    movers: list[dict[str, Any]] = []
    for a in assets:
        if not a.coingecko_id:
            continue
        rows = (
            await session.execute(
                select(PriceSnapshot)
                .where(
                    PriceSnapshot.coingecko_id == a.coingecko_id,
                    PriceSnapshot.ts >= since,
                )
                .order_by(PriceSnapshot.ts)
            )
        ).scalars().all()
        if len(rows) < 2:
            continue
        first, last = rows[0], rows[-1]
        change = _pct(float(last.price_usd), float(first.price_usd))
        if change is None:
            continue
        movers.append(
            {"symbol": a.symbol, "price_usd": float(last.price_usd), "change_pct": change}
        )
    movers.sort(key=lambda m: abs(m["change_pct"]), reverse=True)
    return movers


async def _tvl_shifts(session: AsyncSession, assets: list[Watchlist]) -> list[dict[str, Any]]:
    since = datetime.now(tz=UTC) - _LOOKBACK
    shifts: list[dict[str, Any]] = []
    for a in assets:
        if not a.defillama_slug:
            continue
        rows = (
            await session.execute(
                select(TvlSnapshot)
                .where(
                    TvlSnapshot.defillama_slug == a.defillama_slug,
                    TvlSnapshot.ts >= since,
                )
                .order_by(TvlSnapshot.ts)
            )
        ).scalars().all()
        if len(rows) < 2:
            continue
        first, last = rows[0], rows[-1]
        change = _pct(float(last.tvl_usd), float(first.tvl_usd))
        if change is None:
            continue
        shifts.append(
            {"name": a.name, "tvl_usd": float(last.tvl_usd), "change_pct": change}
        )
    shifts.sort(key=lambda s: abs(s["change_pct"]), reverse=True)
    return shifts


async def _unlocks(session: AsyncSession) -> list[dict[str, Any]]:
    now = datetime.now(tz=UTC)
    horizon = now + timedelta(days=7)
    rows = (
        await session.execute(
            select(UnlockEvent, Watchlist.symbol)
            .join(Watchlist, UnlockEvent.watchlist_id == Watchlist.id)
            .where(UnlockEvent.unlock_date >= now, UnlockEvent.unlock_date <= horizon)
            .order_by(UnlockEvent.unlock_date)
        )
    ).all()
    return [
        {
            "symbol": symbol,
            "date": ev.unlock_date.date().isoformat(),
            "amount_usd": float(ev.amount_usd) if ev.amount_usd is not None else None,
            "amount_tokens": float(ev.amount_tokens) if ev.amount_tokens is not None else None,
            "description": ev.description,
        }
        for ev, symbol in rows
    ]


async def _regulatory(assets: list[Watchlist]) -> dict[str, Any] | None:
    """One retrieval pass over the regulatory collection for watchlist context."""
    symbols = ", ".join(a.symbol for a in assets) or "crypto-assets"
    query = f"recent regulatory requirements relevant to {symbols} under MiCA and FINMA"
    try:
        vector = await asyncio.to_thread(embed_query, query)
        hits = await search_regulatory(vector, top_k=3)
    except Exception as exc:  # noqa: BLE001 - regulatory pass is best-effort
        logger.warning('{"job":"daily_brief","warn":"regulatory pass failed","error":"%s"}', exc)
        return None
    if not hits:
        return None
    score, payload = hits[0]
    return {
        "document": payload["document"],
        "ref": payload["ref"],
        "url": payload["url"],
        "excerpt": payload["text"],
        "score": round(score, 4),
    }


def _render_data_block(sections: dict[str, Any]) -> str:
    import json

    return json.dumps(sections, indent=2, ensure_ascii=False)


async def build_brief(session: AsyncSession) -> Brief:
    assets = (
        await session.execute(select(Watchlist).order_by(Watchlist.symbol))
    ).scalars().all()
    assets = list(assets)

    sections: dict[str, Any] = {
        "movers": await _movers(session, assets),
        "tvl_shifts": await _tvl_shifts(session, assets),
        "unlocks": await _unlocks(session),
        "regulatory": await _regulatory(assets),
    }

    today = datetime.now(tz=UTC)
    brief_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str = brief_date.date().isoformat()
    user_prompt = (
        f"DATA (date {date_str}):\n\n{_render_data_block(sections)}\n\n"
        "Write the daily brief from this data only."
    )
    body = await generate(load_prompt("daily_brief_v1"), user_prompt)

    stmt = (
        insert(Brief)
        .values(brief_date=brief_date, sections=sections, body_markdown=body)
        .on_conflict_do_update(
            index_elements=[Brief.brief_date],
            set_={"sections": sections, "body_markdown": body},
        )
        .returning(Brief)
    )
    brief = (await session.execute(stmt)).scalar_one()
    await session.commit()
    logger.info('{"job":"daily_brief","event":"stored","date":"%s"}', date_str)
    return brief


async def run_daily_brief() -> None:
    async with SessionLocal() as session:
        try:
            brief = await build_brief(session)
        except LLMError as exc:
            logger.error('{"job":"daily_brief","error":"llm unavailable","detail":"%s"}', exc)
            return
        try:
            subject = f"Argus Daily Brief — {brief.brief_date.date().isoformat()}"
            send_email(subject, brief.body_markdown)
        except EmailNotConfigured as exc:
            logger.warning('{"job":"daily_brief","warn":"email skipped","detail":"%s"}', exc)
            return
        brief.emailed_at = datetime.now(tz=UTC)
        await session.commit()
