from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from argus_core.models import (
    Base,
    Brief,
    PriceSnapshot,
    UnlockEvent,
    Watchlist,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import brief, jobs


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_pct() -> None:
    assert brief._pct(110, 100) == 10.0
    assert brief._pct(90, 100) == -10.0
    assert brief._pct(5, 0) is None


@pytest.mark.asyncio
async def test_movers_sorted_by_abs_change(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    session.add_all(
        [
            Watchlist(symbol="BTC", name="Bitcoin", coingecko_id="bitcoin"),
            Watchlist(symbol="ETH", name="Ethereum", coingecko_id="ethereum"),
        ]
    )
    session.add_all(
        [
            PriceSnapshot(coingecko_id="bitcoin", ts=now - timedelta(hours=24), price_usd=100),
            PriceSnapshot(coingecko_id="bitcoin", ts=now, price_usd=101),
            PriceSnapshot(coingecko_id="ethereum", ts=now - timedelta(hours=24), price_usd=100),
            PriceSnapshot(coingecko_id="ethereum", ts=now, price_usd=90),
        ]
    )
    await session.commit()

    assets = list((await session.execute(__import__("sqlalchemy").select(Watchlist))).scalars())
    movers = await brief._movers(session, assets)
    assert [m["symbol"] for m in movers] == ["ETH", "BTC"]  # |−10| > |+1|
    assert movers[0]["change_pct"] == -10.0


@pytest.mark.asyncio
async def test_unlocks_within_window(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    wl = Watchlist(symbol="UNI", name="Uniswap", coingecko_id="uniswap")
    session.add(wl)
    await session.flush()
    session.add_all(
        [
            UnlockEvent(
                watchlist_id=wl.id, unlock_date=now + timedelta(days=3), amount_usd=1_000_000
            ),
            UnlockEvent(
                watchlist_id=wl.id, unlock_date=now + timedelta(days=30), amount_usd=2_000_000
            ),
        ]
    )
    await session.commit()

    unlocks = await brief._unlocks(session)
    assert len(unlocks) == 1
    assert unlocks[0]["symbol"] == "UNI"


@pytest.mark.asyncio
async def test_run_daily_brief_emails_generated_body(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, str] = {}
    fake = Brief(
        brief_date=datetime(2026, 7, 10, tzinfo=UTC),
        sections={},
        body_markdown="# Daily Brief",
    )

    async def fake_build(_session: AsyncSession) -> Brief:
        return fake

    def fake_send(subject: str, body: str) -> None:
        sent["subject"] = subject
        sent["body"] = body

    class _Ctx:
        async def __aenter__(self) -> object:
            class _S:
                async def commit(self) -> None:
                    return None

            return _S()

        async def __aexit__(self, *a: object) -> None:
            return None

    monkeypatch.setattr(brief, "SessionLocal", lambda: _Ctx())
    monkeypatch.setattr(brief, "build_brief", fake_build)
    monkeypatch.setattr(brief, "send_email", fake_send)

    await brief.run_daily_brief()
    assert sent["body"] == "# Daily Brief"
    assert "2026-07-10" in sent["subject"]
    assert fake.emailed_at is not None


def test_daily_brief_job_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def fake_run() -> None:
        nonlocal called
        called = True

    import app.brief as brief_mod

    monkeypatch.setattr(brief_mod, "run_daily_brief", fake_run)
    jobs.daily_brief()
    assert called
