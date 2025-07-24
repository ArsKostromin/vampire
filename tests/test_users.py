import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import logging

logger = logging.getLogger("test")

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(base_url="http://test", transport=ASGITransport(app=app)) as ac:
        # Регистрация
        resp = await ac.post("/users/register", json={"name": "testuser", "password": "testpass"})
        if resp.status_code != 201:
            logger.error("/users/register response: %s", resp.text)
            try:
                logger.error("/users/register response (json): %s", resp.json())
            except Exception:
                pass
        assert resp.status_code == 201
        user = resp.json()
        assert user["name"] == "testuser"
        # Логин
        resp = await ac.post("/users/login", json={"name": "testuser", "password": "testpass"})
        assert resp.status_code == 200
        tokens = resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        # Получение информации о себе
        resp = await ac.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            logger.error("/users/me response: %s", resp.text)
            try:
                logger.error("/users/me response (json): %s", resp.json())
            except Exception:
                pass
        assert resp.status_code == 200
        me = resp.json()
        assert me["name"] == "testuser"

@pytest.mark.asyncio
async def test_leaderboard_and_update_record():
    async with AsyncClient(base_url="http://test", transport=ASGITransport(app=app)) as ac:
        # Логин
        resp = await ac.post("/users/login", json={"name": "testuser", "password": "testpass"})
        tokens = resp.json()
        access_token = tokens["access_token"]
        # Обновление рекорда
        resp = await ac.patch("/users/record", json={"record": 42.0}, headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_record"] == 42.0
        # Лидерборд
        resp = await ac.get("/users/leaderboard")
        assert resp.status_code == 200
        leaderboard = resp.json()
        assert any(u["name"] == "testuser" for u in leaderboard) 