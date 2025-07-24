import pytest
from httpx import AsyncClient
from uuid import UUID

USERNAME = "testuser"
PASSWORD = "testpass123"

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/register", json={"name": USERNAME, "password": PASSWORD})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data and "name" in data
    assert data["name"] == USERNAME
    assert UUID(data["id"])  # проверка что это UUID

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    response = await client.post("/login", json={"name": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data and "refresh_token" in data
    assert data["token_type"] == "bearer"
    global ACCESS_TOKEN, REFRESH_TOKEN
    ACCESS_TOKEN = data["access_token"]
    REFRESH_TOKEN = data["refresh_token"]

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = await client.get("/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == USERNAME
    assert isinstance(data["record"], float)

@pytest.mark.asyncio
async def test_update_record(client: AsyncClient):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = await client.patch("/record", headers=headers, json={"record": 123.45})
    assert response.status_code == 200
    data = response.json()
    assert data["old_record"] <= data["new_record"]
    assert data["new_record"] == 123.45

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    response = await client.post("/refresh", json={"refresh_token": REFRESH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_leaderboard(client: AsyncClient):
    response = await client.get("/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(user["name"] == USERNAME for user in data)
