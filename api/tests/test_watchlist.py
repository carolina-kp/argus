from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/watchlist")
    assert resp.status_code == 401


async def test_crud_flow(client: AsyncClient) -> None:
    # Empty at first.
    resp = await client.get("/watchlist", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []

    # Create.
    resp = await client.post(
        "/watchlist",
        headers=auth_headers(),
        json={"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    )
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Duplicate symbol conflicts.
    dup = await client.post(
        "/watchlist", headers=auth_headers(), json={"symbol": "BTC", "name": "Bitcoin"}
    )
    assert dup.status_code == 409

    # Update.
    patch = await client.patch(
        f"/watchlist/{item_id}", headers=auth_headers(), json={"name": "BTC renamed"}
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "BTC renamed"

    # Delete.
    delete = await client.delete(f"/watchlist/{item_id}", headers=auth_headers())
    assert delete.status_code == 204
    assert (await client.get("/watchlist", headers=auth_headers())).json() == []
