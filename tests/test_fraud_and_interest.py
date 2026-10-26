async def test_large_transaction_flagged(client, auth, make_account):
    acc = await make_account(balance=500000)
    r = await client.post("/transactions/withdraw", headers=auth, json={"account_no": acc["account_no"], "amount": 150000})
    body = r.json()
    assert body["status"] == "Flagged"
    assert any("threshold" in f for f in body["fraud_flags"])


async def test_small_transaction_not_flagged(client, auth, make_account):
    acc = await make_account(balance=1000)
    r = await client.post("/transactions/deposit", headers=auth, json={"account_no": acc["account_no"], "amount": 10})
    assert r.json()["status"] == "Success"


async def test_velocity_rule_flags_rapid_transactions(client, auth, make_account):
    acc = await make_account(balance=100000)
    last = None
    for i in range(6):  # different amounts, so only the velocity rule can fire
        last = await client.post("/transactions/deposit", headers=auth, json={"account_no": acc["account_no"], "amount": 10 + i})
    assert last.json()["status"] == "Flagged"
    assert any("within" in f for f in last.json()["fraud_flags"])


async def test_duplicate_rule_flags_repeat(client, auth, make_account):
    acc = await make_account(balance=1000)
    payload = {"account_no": acc["account_no"], "amount": 77}
    await client.post("/transactions/deposit", headers=auth, json=payload)
    second = await client.post("/transactions/deposit", headers=auth, json=payload)
    assert any("duplicate" in f.lower() for f in second.json()["fraud_flags"])


async def test_fraud_alerts_endpoint_lists_flagged(client, auth, make_account):
    acc = await make_account(balance=500000)
    await client.post("/transactions/withdraw", headers=auth, json={"account_no": acc["account_no"], "amount": 150000})
    alerts = (await client.get("/fraud/alerts", headers=auth)).json()
    assert len(alerts) == 1 and alerts[0]["status"] == "Flagged"


async def test_interest_credits_savings_only(client, auth, admin_auth, make_account):
    sav = await make_account("Asha Rao", 10000, "Savings")
    cur = await make_account("Bala Nair", 10000, "Current")
    r = await client.post("/interest/run", headers=admin_auth, json={"annual_rate_percent": 12, "period_years": 1})
    assert r.status_code == 200 and r.json()["accounts_credited"] == 1
    assert (await client.get(f"/accounts/{sav['account_no']}", headers=auth)).json()["balance"] == 11200
    assert (await client.get(f"/accounts/{cur['account_no']}", headers=auth)).json()["balance"] == 10000


async def test_interest_requires_privileged_role(client, auth):
    r = await client.post("/interest/run", headers=auth, json={"annual_rate_percent": 4, "period_years": 1})
    assert r.status_code == 403


async def test_genai_analysis_without_key_degrades_gracefully(client, auth, make_account):
    acc = await make_account(balance=1000)
    await client.post("/transactions/deposit", headers=auth, json={"account_no": acc["account_no"], "amount": 10})
    r = await client.post("/analysis/account", headers=auth, json={"account_no": acc["account_no"]})
    assert r.status_code == 200 and r.json()["risk_level"] == "unknown"
