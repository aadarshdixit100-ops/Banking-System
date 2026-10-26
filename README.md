# Ledgerline Bank — Banking Management System

Full-stack banking application:
FastAPI REST APIs · MongoDB · Redis caching · rule-based fraud detection ·
GenAI-powered transaction analysis · responsive HTML/CSS/JS frontend.

## What's implemented

- **Account management** — create customers/accounts, list, fetch, close (`app/routers/accounts.py`)
- **Deposits, withdrawals, fund transfers, transaction processing** — with balance
  validation and atomic-per-request updates (`app/routers/transactions.py`)
- **Automated interest calculation** — simple interest credited as a Deposit
  transaction, compounding on the next cycle (`app/services/interest_service.py`)
- **Secure authentication** — JWT bearer tokens, bcrypt password hashing, role-based
  route protection (`app/core/security.py`, `app/routers/auth.py`)
- **Transaction validation & reliable state management** — active-account checks,
  sufficient-funds checks, MongoDB unique indexes, incrementing counters for
  account/txn IDs (`app/db/mongodb.py`)
- **Redis caching** — account lookups are cached (`app/db/redis_client.py`) and
  invalidated on every balance-changing operation; also powers the sliding-window
  velocity counter used by fraud detection
- **Rule-based fraud detection** — large-transaction, velocity, and duplicate-entry
  rules (`app/services/fraud_detection.py`)
- **GenAI-powered transaction analysis** — sends an account's recent transaction
  history to Claude for a plain-English risk narrative, as a second opinion next
  to the deterministic rules (`app/services/genai_service.py`,
  `app/routers/analysis.py`)
- **Responsive frontend** — `frontend/BankingSystem.html`: real-time balance
  updates, transaction history with filtering, a deposit/withdrawal/transfer
  chart, and a "GenAI Transaction Analysis" panel on the Fraud Alerts page that
  calls the `/analysis/account` endpoint above

## Project layout

```
banking-system/
├── app/
│   ├── main.py                 FastAPI app, CORS, router wiring, startup/shutdown
│   ├── core/
│   │   ├── config.py           Settings (env-driven)
│   │   └── security.py         Password hashing, JWT, auth dependencies
│   ├── db/
│   │   ├── mongodb.py          Motor async client + indexes
│   │   └── redis_client.py     Redis client + cache + rate-window helpers
│   ├── models/schemas.py       Pydantic request/response models
│   ├── services/
│   │   ├── fraud_detection.py  Rule-based fraud checks
│   │   ├── interest_service.py Interest calculation
│   │   └── genai_service.py    Anthropic API call for transaction analysis
│   └── routers/
│       ├── auth.py, accounts.py, transactions.py, interest.py, fraud.py, analysis.py
├── frontend/
│   └── BankingSystem.html      Standalone responsive frontend
├── requirements.txt
├── Dockerfile
├── docker-compose.yml          api + mongo + redis
└── .env.example
```

## Running it

### 1. With Docker (recommended)

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY if you want GenAI analysis to work
docker compose up --build
```

API is now at `http://localhost:8000` (interactive docs at `/docs`).

### 2. Locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point MONGO_URI / REDIS_URL at your local instances

uvicorn app.main:app --reload
```

You'll need MongoDB and Redis running locally (e.g. `mongod` and `redis-server`,
or `docker run -p 27017:27017 mongo:7` / `docker run -p 6379:6379 redis:7-alpine`).

### 3. Frontend

Open `frontend/BankingSystem.html` in a browser. On the Dashboard, use the
**Backend API** card: enter the API URL, then *Register & Log In* (first time) or
*Log In*. Once connected, accounts, deposits, withdrawals, transfers, interest,
fraud flags and history all run through the REST API and are stored in MongoDB.
Without connecting, the page runs as a standalone demo on browser storage.
The GenAI panel on the Fraud Alerts page uses the same connection.

Note: interest runs need an Administrator or Branch Manager login.

### 4. Tests

```bash
pip install -r requirements.txt
pytest
```

The suite uses in-memory MongoDB (`mongomock-motor`) and Redis (`fakeredis`), so no
services are needed. It covers auth, deposits/withdrawals/transfers, validation,
history filters, cache invalidation, each fraud rule, interest, and role checks.

## API quick reference

| Method | Path                     | Purpose                                   |
|--------|--------------------------|--------------------------------------------|
| POST   | `/auth/register`         | Create a staff user                        |
| POST   | `/auth/login`            | OAuth2 password login → JWT                |
| GET    | `/auth/me`               | Current user                               |
| POST   | `/accounts`              | Open a new customer + account              |
| GET    | `/accounts`              | List accounts                              |
| GET    | `/accounts/{account_no}` | Get one account (Redis-cached)             |
| POST   | `/accounts/{no}/close`   | Close a zero-balance account               |
| POST   | `/transactions/deposit`  | Deposit                                    |
| POST   | `/transactions/withdraw` | Withdrawal (checks sufficient funds)       |
| POST   | `/transactions/transfer` | Transfer between two accounts              |
| GET    | `/transactions`          | History, filterable by account/type/date/min amount |
| POST   | `/interest/run`          | Run an interest cycle over savings accounts (admin/manager only) |
| GET    | `/fraud/alerts`          | Transactions flagged by the rule engine    |
| POST   | `/analysis/account`      | GenAI risk read on an account's recent activity |

All routes except `/auth/register` and `/auth/login` require
`Authorization: Bearer <token>`.

## Notes

- The fraud rule-engine thresholds (`FRAUD_LARGE_TXN_AMOUNT`,
  `FRAUD_VELOCITY_COUNT`, `FRAUD_VELOCITY_WINDOW_SECONDS`) are configurable via
  `.env`.
- `ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5` — change it in `.env` to
  whatever model you have access to.
- CORS is wide open (`allow_origins=["*"]`) for local development; restrict it
  before deploying.
