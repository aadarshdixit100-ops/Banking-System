from fastapi import APIRouter, Depends

from app.core.security import get_current_user, require_role
from app.db.mongodb import get_db
from app.models.schemas import InterestRunRequest
from app.routers.transactions import _next_txn_id
from app.services.interest_service import apply_interest

router = APIRouter(prefix="/interest", tags=["interest"])


@router.post("/run")
async def run_interest_cycle(payload: InterestRunRequest, user=Depends(require_role("Administrator", "Branch Manager"))):
    db = get_db()

    async def _next():
        return await _next_txn_id(db)

    results = await apply_interest(db, payload.annual_rate_percent, payload.period_years, _next)
    return {"accounts_credited": len(results), "details": results}
