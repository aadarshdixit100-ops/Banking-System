from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.db.mongodb import get_db
from app.models.schemas import TransactionAnalysisRequest
from app.services.genai_service import analyze_account_activity

router = APIRouter(prefix="/analysis", tags=["genai-analysis"])


@router.post("/account")
async def analyze_account(payload: TransactionAnalysisRequest, user=Depends(get_current_user)):
    db = get_db()

    account_no = payload.account_no
    if account_no is None and payload.txn_id is not None:
        txn = await db.transactions.find_one({"txn_id": payload.txn_id})
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        account_no = txn["account_no"]

    if account_no is None:
        raise HTTPException(status_code=400, detail="Provide account_no or txn_id")

    cursor = db.transactions.find({"account_no": account_no}).sort("created_at", -1).limit(payload.lookback)
    txns = await cursor.to_list(length=payload.lookback)
    if not txns:
        raise HTTPException(status_code=404, detail="No transactions found for that account")

    result = await analyze_account_activity(account_no, txns)
    return {"account_no": account_no, "transactions_considered": len(txns), **result}
