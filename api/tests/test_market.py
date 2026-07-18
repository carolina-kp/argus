from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_market_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/market/prices/ethereum")).status_code == 401


async def test_price_history_empty(client: AsyncClient) -> None:
    resp = await client.get("/market/prices/ethereum", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


async def test_onchain_latest_404_when_empty(client: AsyncClient) -> None:
    resp = await client.get("/onchain/btc/latest", headers=auth_headers())
    assert resp.status_code == 404


async def test_days_query_validation(client: AsyncClient) -> None:
    resp = await client.get("/market/tvl/aave?days=999", headers=auth_headers())
    assert resp.status_code == 422


async def test_unlocks_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/market/unlocks")).status_code == 401


async def test_unlocks_empty(client: AsyncClient) -> None:
    resp = await client.get("/market/unlocks", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []
