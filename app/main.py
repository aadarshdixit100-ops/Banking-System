from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import mongodb, redis_client
from app.routers import accounts, analysis, auth, fraud, interest, transactions

app = FastAPI(
    title="Ledgerline Bank API",
    description=(
        "REST APIs for account management, deposits, withdrawals, fund transfers, "
        "transaction processing, automated interest calculation, rule-based fraud "
        "detection and GenAI-powered transaction analysis."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(interest.router)
app.include_router(fraud.router)
app.include_router(analysis.router)


@app.on_event("startup")
async def on_startup():
    mongodb.connect()
    redis_client.connect()
    await mongodb.ensure_indexes()


@app.on_event("shutdown")
async def on_shutdown():
    mongodb.close()
    redis_client.close()


@app.get("/health")
async def health():
    return {"status": "ok"}
