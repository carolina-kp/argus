from datetime import UTC, datetime, timedelta

from argus_core.models import Anomaly, Brief
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.conftest import auth_headers


async def test_briefs_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/briefs")).status_code == 401


async def test_anomalies_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/anomalies")).status_code == 401


async def test_list_and_get_brief(
    client_db: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = client_db
    day = datetime(2026, 7, 10, tzinfo=UTC)
    async with factory() as s:
        s.add(
            Brief(
                brief_date=day,
                sections={"movers": []},
                body_markdown="# Daily Brief",
            )
        )
        await s.commit()

    listed = await client.get("/briefs", headers=auth_headers())
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert "body_markdown" not in listed.json()[0]  # summary omits body

    detail = await client.get("/briefs/2026-07-10", headers=auth_headers())
    assert detail.status_code == 200
    assert detail.json()["body_markdown"] == "# Daily Brief"

    assert (await client.get("/briefs/2026-01-01", headers=auth_headers())).status_code == 404


async def test_anomalies_feed_filters_by_kind(
    client_db: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = client_db
    now = datetime.now(tz=UTC)
    async with factory() as s:
        s.add_all(
            [
                Anomaly(kind="zscore", symbol="AAVE", metric="return", zscore=4.1,
                        value=0.3, ts=now, detail={}, dedupe_key="zscore:AAVE:return:x"),
                Anomaly(kind="depeg", symbol="USDC", metric="price", zscore=None,
                        value=-0.01, ts=now, detail={}, dedupe_key="depeg:USDC:price:x"),
                Anomaly(kind="zscore", symbol="ETH", metric="volume", zscore=5.0,
                        value=9e9, ts=now - timedelta(days=30), detail={},
                        dedupe_key="zscore:ETH:volume:old"),
            ]
        )
        await s.commit()

    all_recent = await client.get("/anomalies?days=7", headers=auth_headers())
    assert all_recent.status_code == 200
    assert len(all_recent.json()) == 2  # the 30-day-old one is outside the window

    depegs = await client.get("/anomalies?kind=depeg", headers=auth_headers())
    assert [a["symbol"] for a in depegs.json()] == ["USDC"]


async def test_trigger_ingest_sets_flag(
    client_db: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch,
) -> None:
    client, _ = client_db
    captured: dict[str, str] = {}

    async def fake_request(requested_at: str) -> None:
        captured["at"] = requested_at

    import app.routers.admin as admin_mod

    monkeypatch.setattr(admin_mod, "request_ingest", fake_request)
    resp = await client.post("/admin/ingest", headers=auth_headers())
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"
    assert "at" in captured
