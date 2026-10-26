import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.db import mongodb, redis_client
from app.main import app


@pytest.fixture(autouse=True)
def fake_backends():
    """Fresh in-memory MongoDB and Redis for every test (no services needed)."""
    mongodb._client = AsyncMongoMockClient()
    redis_client._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield
    mongodb._client = None
    redis_client._redis = None


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _login(client, username: str, role: str) -> dict:
    await client.post(
        "/auth/register",
        json={"username": username, "password": "pass1234", "full_name": username.title(), "role": role},
    )
    res = await client.post("/auth/login", data={"username": username, "password": "pass1234"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
async def auth(client):
    return await _login(client, "teller1", "Teller")


@pytest.fixture
async def admin_auth(client):
    return await _login(client, "admin1", "Administrator")


@pytest.fixture
def make_account(client, auth):
    async def _make(name="Asha Rao", balance=1000, account_type="Savings"):
        res = await client.post(
            "/accounts",
            headers=auth,
            json={
                "customer": {"full_name": name, "email": f"{name.split()[0].lower()}@example.com", "phone": "9999999999"},
                "account_type": account_type,
                "opening_deposit": balance,
            },
        )
        assert res.status_code == 201, res.text
        return res.json()

    return _make
