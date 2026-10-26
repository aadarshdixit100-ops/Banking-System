async def test_deposit_increases_balance(client, auth, make_account):
    acc = await make_account(balance=1000)
    r = await client.post("/transactions/deposit", headers=auth, json={"account_no": acc["account_no"], "amount": 500})
    assert r.status_code == 201
    assert r.json()["balance_after"] == 1500


async def test_withdraw_decreases_balance(client, auth, make_account):
    acc = await make_account(balance=1000)
    r = await client.post("/transactions/withdraw", headers=auth, json={"account_no": acc["account_no"], "amount": 400})
    assert r.status_code == 201
    assert r.json()["balance_after"] == 600


async def test_withdraw_insufficient_funds(client, auth, make_account):
    acc = await make_account(balance=100)
    r = await client.post("/transactions/withdraw", headers=auth, json={"account_no": acc["account_no"], "amount": 500})
    assert r.status_code == 400
    assert "Insufficient" in r.json()["detail"]


async def test_negative_amount_rejected(client, auth, make_account):
    acc = await make_account()
    r = await client.post("/transactions/deposit", headers=auth, json={"account_no": acc["account_no"], "amount": -5})
    assert r.status_code == 422


async def test_unknown_account_404(client, auth):
    r = await client.post("/transactions/deposit", headers=auth, json={"account_no": 999999, "amount": 10})
    assert r.status_code == 404


async def test_transfer_moves_money(client, auth, make_account):
    a = await make_account("Asha Rao", 1000)
    b = await make_account("Bala Nair", 200)
    r = await client.post(
        "/transactions/transfer", headers=auth,
        json={"from_account_no": a["account_no"], "to_account_no": b["account_no"], "amount": 300},
    )
    assert r.status_code == 201
    assert (await client.get(f"/accounts/{a['account_no']}", headers=auth)).json()["balance"] == 700
    assert (await client.get(f"/accounts/{b['account_no']}", headers=auth)).json()["balance"] == 500


async def test_transfer_to_same_account_rejected(client, auth, make_account):
    a = await make_account()
    r = await client.post(
        "/transactions/transfer", headers=auth,
        json={"from_account_no": a["account_no"], "to_account_no": a["account_no"], "amount": 10},
    )
    assert r.status_code == 400


async def test_history_filters(client, auth, make_account):
    acc = await make_account(balance=1000)
    n = acc["account_no"]
    await client.post("/transactions/deposit", headers=auth, json={"account_no": n, "amount": 50})
    await client.post("/transactions/withdraw", headers=auth, json={"account_no": n, "amount": 20})
    deposits = (await client.get("/transactions", headers=auth, params={"account_no": n, "type": "Deposit"})).json()
    assert [t["type"] for t in deposits] == ["Deposit"]
    big = (await client.get("/transactions", headers=auth, params={"account_no": n, "min_amount": 30})).json()
    assert [t["amount"] for t in big] == [50]


async def test_balance_cache_invalidated_after_deposit(client, auth, make_account):
    acc = await make_account(balance=100)
    n = acc["account_no"]
    assert (await client.get(f"/accounts/{n}", headers=auth)).json()["balance"] == 100  # primes cache
    await client.post("/transactions/deposit", headers=auth, json={"account_no": n, "amount": 50})
    assert (await client.get(f"/accounts/{n}", headers=auth)).json()["balance"] == 150
