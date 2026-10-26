async def test_register_and_login(client):
    r = await client.post("/auth/register", json={"username": "sam", "password": "pw12345", "full_name": "Sam"})
    assert r.status_code == 201
    r = await client.post("/auth/login", data={"username": "sam", "password": "pw12345"})
    assert r.status_code == 200 and "access_token" in r.json()


async def test_duplicate_username_rejected(client):
    body = {"username": "sam", "password": "pw12345", "full_name": "Sam"}
    await client.post("/auth/register", json=body)
    assert (await client.post("/auth/register", json=body)).status_code == 409


async def test_wrong_password_rejected(client):
    await client.post("/auth/register", json={"username": "sam", "password": "pw12345", "full_name": "Sam"})
    r = await client.post("/auth/login", data={"username": "sam", "password": "wrong"})
    assert r.status_code == 401


async def test_protected_route_requires_token(client):
    assert (await client.get("/accounts")).status_code == 401


async def test_password_is_hashed_in_db(client):
    from app.db.mongodb import get_db
    await client.post("/auth/register", json={"username": "sam", "password": "pw12345", "full_name": "Sam"})
    user = await get_db().users.find_one({"username": "sam"})
    assert user["password_hash"] != "pw12345"
