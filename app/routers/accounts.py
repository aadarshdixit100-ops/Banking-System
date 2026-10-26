from pymongo import ReturnDocument
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.db.mongodb import get_db
from app.db.redis_client import cache_delete, cache_get, cache_set
from app.models.schemas import AccountCreate, AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


async def _next_account_no(db) -> int:
    counter = await db.counters.find_one_and_update(
        {"_id": "account_no"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return 100000 + counter["seq"]


@router.post("", response_model=AccountOut, status_code=201)
async def create_account(payload: AccountCreate, user=Depends(get_current_user)):
    db = get_db()

    customer_doc = {
        "full_name": payload.customer.full_name,
        "email": payload.customer.email,
        "phone": payload.customer.phone,
        "created_at": datetime.now(timezone.utc),
    }
    customer_result = await db.customers.insert_one(customer_doc)
    customer_id = str(customer_result.inserted_id)

    account_no = await _next_account_no(db)
    account_doc = {
        "account_no": account_no,
        "customer_id": customer_id,
        "customer_name": payload.customer.full_name,
        "account_type": payload.account_type.value,
        "balance": payload.opening_deposit,
        "status": "Active",
        "created_at": datetime.now(timezone.utc),
    }
    await db.accounts.insert_one(account_doc)

    return AccountOut(**account_doc)


@router.get("", response_model=list[AccountOut])
async def list_accounts(user=Depends(get_current_user)):
    db = get_db()
    accounts = await db.accounts.find().sort("account_no", 1).to_list(length=1000)
    return [AccountOut(**a) for a in accounts]


@router.get("/{account_no}", response_model=AccountOut)
async def get_account(account_no: int, user=Depends(get_current_user)):
    cached = await cache_get(f"account:{account_no}")
    if cached:
        return AccountOut(**cached)

    db = get_db()
    account = await db.accounts.find_one({"account_no": account_no})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.pop("_id", None)
    await cache_set(f"account:{account_no}", account)
    return AccountOut(**account)


@router.post("/{account_no}/close", response_model=AccountOut)
async def close_account(account_no: int, user=Depends(get_current_user)):
    db = get_db()
    account = await db.accounts.find_one({"account_no": account_no})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account["balance"] != 0:
        raise HTTPException(status_code=400, detail="Balance must be zero before closing")

    await db.accounts.update_one({"account_no": account_no}, {"$set": {"status": "Closed"}})
    await cache_delete(f"account:{account_no}")
    account["status"] = "Closed"
    account.pop("_id", None)
    return AccountOut(**account)
