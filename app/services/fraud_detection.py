"""Rule-based fraud detection.

Three rules are evaluated on every transaction:
  1. Large single transaction above a configured threshold.
  2. Velocity: too many transactions on the same account in a short rolling
     window (tracked in Redis with a sorted set so it works across processes).
  3. Likely duplicate: same account + amount + type submitted again within a
     few seconds (common with double form submissions or replay attempts).
"""

from app.core.config import settings
from app.db.redis_client import rate_window_count


async def evaluate_transaction(db, account_no: int, amount: float, txn_type: str) -> list[str]:
    flags: list[str] = []

    # Rule 1: large transaction
    if amount >= settings.fraud_large_txn_amount:
        flags.append(f"Single transaction over the ₹{settings.fraud_large_txn_amount:,.0f} threshold")

    # Rule 2: velocity — too many transactions on this account, recently
    velocity_key = f"fraud:velocity:{account_no}"
    count = await rate_window_count(velocity_key, settings.fraud_velocity_window_seconds)
    if count >= settings.fraud_velocity_count:
        flags.append(
            f"{count}+ transactions on account {account_no} within "
            f"{settings.fraud_velocity_window_seconds} seconds"
        )

    # Rule 3: likely duplicate — same account/amount/type in the last 30s
    recent = await db.transactions.find_one(
        {
            "account_no": account_no,
            "amount": amount,
            "type": txn_type,
        },
        sort=[("created_at", -1)],
    )
    if recent is not None:
        from datetime import datetime, timezone

        age = (datetime.now(timezone.utc) - recent["created_at"].replace(tzinfo=timezone.utc)).total_seconds()
        if age <= 30:
            flags.append("Likely duplicate of a transaction submitted moments ago")

    return flags
