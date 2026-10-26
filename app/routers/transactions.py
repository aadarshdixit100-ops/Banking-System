from pymongo import ReturnDocument
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.db.mongodb import get_db
from app.db.redis_client import cache_delete
from app.models.schemas import DepositRequest, TransactionOut, TransferRequest, TxnType, WithdrawalRequest
from app.services.fraud_detection import evaluate_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _next_txn_id(db) -> int:
    counter = await db.counters.find_one_and_update(
        {"_id": "txn_id"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return 1000 + counter["seq"]


async def _get_active_account(db, account_no: int) -> dict:
    account = await db.accounts.find_one({"account_no": account_no})
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_no} not found")
    if account["status"] != "Active":
        raise HTTPException(status_code=400, detail=f"Account {account_no} is not active")
    return account


async def _record_transaction(
    db, account_no: int, amount: float, txn_type: str, balance_after: float,
    counterparty: Optional[int] = None, note: Optional[str] = None,
) -> TransactionOut:
    flags = await evaluate_transaction(db, account_no, amount, txn_type)
    txn_id = await _next_txn_id(db)

    doc = {
        "txn_id": txn_id,
        "account_no": account_no,
        "counterparty_account_no": counterparty,
        "type": txn_type,
        "amount": amount,
        "balance_after": balance_after,
        "status": "Flagged" if flags else "Success",
        "fraud_flags": flags,
        "note": note,
        "created_at": datetime.now(timezone.utc),
    }
    await db.transactions.insert_one(doc)
    await cache_delete(f"account:{account_no}")
    return TransactionOut(**doc)


@router.post("/deposit", response_model=TransactionOut, status_code=201)
async def deposit(payload: DepositRequest, user=Depends(get_current_user)):
    db = get_db()
    account = await _get_active_account(db, payload.account_no)
    new_balance = round(account["balance"] + payload.amount, 2)
    await db.accounts.update_one({"account_no": payload.account_no}, {"$set": {"balance": new_balance}})
    return await _record_transaction(db, payload.account_no, payload.amount, TxnType.deposit.value, new_balance, note=payload.note)


@router.post("/withdraw", response_model=TransactionOut, status_code=201)
async def withdraw(payload: WithdrawalRequest, user=Depends(get_current_user)):
    db = get_db()
    account = await _get_active_account(db, payload.account_no)
    if account["balance"] < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    new_balance = round(account["balance"] - payload.amount, 2)
    await db.accounts.update_one({"account_no": payload.account_no}, {"$set": {"balance": new_balance}})
    return await _record_transaction(db, payload.account_no, payload.amount, TxnType.withdrawal.value, new_balance, note=payload.note)


@router.post("/transfer", response_model=list[TransactionOut], status_code=201)
async def transfer(payload: TransferRequest, user=Depends(get_current_user)):
    if payload.from_account_no == payload.to_account_no:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    db = get_db()
    from_acc = await _get_active_account(db, payload.from_account_no)
    to_acc = await _get_active_account(db, payload.to_account_no)

    if from_acc["balance"] < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    from_balance = round(from_acc["balance"] - payload.amount, 2)
    to_balance = round(to_acc["balance"] + payload.amount, 2)

    await db.accounts.update_one({"account_no": payload.from_account_no}, {"$set": {"balance": from_balance}})
    await db.accounts.update_one({"account_no": payload.to_account_no}, {"$set": {"balance": to_balance}})

    debit = await _record_transaction(
        db, payload.from_account_no, payload.amount, TxnType.transfer.value, from_balance,
        counterparty=payload.to_account_no, note=payload.note,
    )
    credit = await _record_transaction(
        db, payload.to_account_no, payload.amount, "Transfer In", to_balance,
        counterparty=payload.from_account_no, note=payload.note,
    )
    return [debit, credit]


@router.get("", response_model=list[TransactionOut])
async def history(
    account_no: Optional[int] = None,
    type: Optional[TxnType] = None,
    min_amount: Optional[float] = Query(default=None, ge=0),
    date: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
    user=Depends(get_current_user),
):
    db = get_db()
    query: dict = {}
    if account_no is not None:
        query["account_no"] = account_no
    if type is not None:
        query["type"] = type.value
    if min_amount is not None:
        query["amount"] = {"$gte": min_amount}
    if date:
        start = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        end = start.replace(hour=23, minute=59, second=59)
        query["created_at"] = {"$gte": start, "$lte": end}

    cursor = db.transactions.find(query).sort("created_at", -1).limit(limit)
    txns = await cursor.to_list(length=limit)
    return [TransactionOut(**t) for t in txns]
