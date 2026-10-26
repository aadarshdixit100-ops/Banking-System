"""Automated interest calculation for savings accounts.

Simple interest = Principal x Rate x Time, credited as a Deposit transaction
so it compounds naturally on the next cycle (it's added to the balance that
the next calculation reads from).
"""

from datetime import datetime, timezone

from app.db.redis_client import cache_delete


async def apply_interest(db, annual_rate_percent: float, period_years: float, next_txn_id_fn) -> list[dict]:
    results = []
    cursor = db.accounts.find({"account_type": "Savings", "status": "Active"})
    async for acc in cursor:
        principal = acc["balance"]
        interest = round(principal * (annual_rate_percent / 100) * period_years, 2)
        if interest <= 0:
            continue

        new_balance = round(principal + interest, 2)
        txn_id = await next_txn_id_fn()

        txn = {
            "txn_id": txn_id,
            "account_no": acc["account_no"],
            "counterparty_account_no": None,
            "type": "Deposit",
            "amount": interest,
            "balance_after": new_balance,
            "status": "Success",
            "fraud_flags": [],
            "note": f"Interest credit @ {annual_rate_percent}% p.a.",
            "created_at": datetime.now(timezone.utc),
        }
        await db.transactions.insert_one(txn)
        await db.accounts.update_one({"account_no": acc["account_no"]}, {"$set": {"balance": new_balance}})
        await cache_delete(f"account:{acc['account_no']}")

        results.append({"account_no": acc["account_no"], "interest_credited": interest, "new_balance": new_balance})

    return results
