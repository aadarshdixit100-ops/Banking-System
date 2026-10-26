from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.db.mongodb import get_db
from app.models.schemas import TransactionOut

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.get("/alerts", response_model=list[TransactionOut])
async def flagged_transactions(user=Depends(get_current_user)):
    db = get_db()
    cursor = db.transactions.find({"status": "Flagged"}).sort("created_at", -1).limit(500)
    txns = await cursor.to_list(length=500)
    return [TransactionOut(**t) for t in txns]
