# Ledgerline Bank — Banking Management System

**A full-stack banking application for account management, transactions, fraud alerts, and AI-assisted transaction analysis.**

![Python](https://img.shields.io/badge/Python-3-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb)
![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis)
![Claude API](https://img.shields.io/badge/AI-Claude%20API-6B4FBB)
![Frontend](https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-E34F26)

Ledgerline Bank is a full-stack banking application built with **FastAPI, MongoDB, Redis, and a responsive HTML/CSS/JavaScript frontend**. It supports account management, deposits, withdrawals, transfers, interest calculations, rule-based fraud detection, and GenAI-powered transaction analysis.

> **Demo and security notice:** This project is intended for learning and demonstration. It is not a production banking platform and must not be used to handle real money or sensitive customer data without a comprehensive security review.

## Tech Stack

| Area | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | MongoDB |
| Caching and velocity counters | Redis |
| Data validation | Pydantic |
| Authentication | JWT bearer tokens, bcrypt password hashing |
| AI-assisted analysis | Anthropic Claude API |
| Frontend | HTML, CSS, JavaScript |
| Containers | Docker, Docker Compose |
| Testing | pytest, mongomock-motor, fakeredis |

## Features

| Area | What it does |
|---|---|
| Account management | Create customers and accounts, list accounts, retrieve account details, and close eligible accounts. |
| Deposits and withdrawals | Process transactions with account-status and balance validation. |
| Fund transfers | Transfer funds between accounts with source-fund checks and transaction records. |
| Interest calculation | Calculate simple interest for savings accounts and record credited interest as a deposit transaction. |
| Authentication and roles | Use JWT bearer tokens, bcrypt password hashing, and role-based route protection. |
| Transaction validation | Validate active accounts and sufficient funds; use MongoDB unique indexes and counters for account and transaction IDs. |
| Redis caching | Cache account lookups, invalidate cache on balance changes, and support sliding-window transaction-velocity counters. |
| Fraud alerts | Flag potentially risky activity using large-transaction, transaction-velocity, and duplicate-entry rules. |
| GenAI transaction analysis | Send recent account transaction history to Claude for a plain-English risk narrative alongside deterministic fraud rules. |
| Transaction history | View transaction records with account/type/date/minimum-amount filtering. |
| Responsive dashboard | Display balances, transaction history, charts, fraud alerts, and GenAI analysis through the frontend. |
| API documentation | Explore and test endpoints through FastAPI's interactive `/docs` interface. |

## Project Structure

```text
banking-system/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router wiring, startup/shutdown
│   ├── core/
│   │   ├── config.py           # Environment-driven settings
│   │   └── security.py         # Password hashing, JWT, auth dependencies
│   ├── db/
│   │   ├── mongodb.py          # MongoDB async client and indexes
│   │   └── redis_client.py     # Redis client, cache, and rate-window helpers
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── fraud_detection.py  # Rule-based fraud checks
│   │   ├── interest_service.py # Interest calculation
│   │   └── genai_service.py    # Anthropic API integration
│   └── routers/
│       ├── auth.py
│       ├── accounts.py
│       ├── transactions.py
│       ├── interest.py
│       ├── fraud.py
│       └── analysis.py
├── frontend/
│   └── BankingSystem.html      # Standalone responsive frontend
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Getting Started

### Option 1: Run with Docker (recommended)

**Prerequisites:** Docker and Docker Compose.

1. Clone the repository and open its directory.
2. Create your local environment file.

   **macOS/Linux**
   ```bash
   cp .env.example .env
   ```

   **Windows PowerShell**
   ```powershell
   Copy-Item .env.example .env
   ```

3. Edit `.env` and configure `ANTHROPIC_API_KEY` if you want GenAI transaction analysis.
4. Build and start the services:

   ```bash
   docker compose up --build
   ```

The API should be available at `http://localhost:8000`. Open `http://localhost:8000/docs` for interactive API documentation.

### Option 2: Run the backend locally

**Prerequisites:** Python, MongoDB, and Redis.

1. Create and activate a virtual environment.

   **Windows PowerShell**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the example environment file.

   **Windows PowerShell**
   ```powershell
   Copy-Item .env.example .env
   ```

   **macOS/Linux**
   ```bash
   cp .env.example .env
   ```

4. Ensure MongoDB and Redis are running, then configure `MONGO_URI` and `REDIS_URL` in `.env`.
5. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

The API should be available at `http://localhost:8000`.

### Option 3: Open the frontend

Open `frontend/BankingSystem.html` in a browser.

On the Dashboard, use the **Backend API** card to enter the API URL and register/log in. Once connected, account and transaction operations use the REST API and MongoDB. Without a backend connection, the page can run as a standalone demo using browser storage.

The GenAI analysis panel is available from the Fraud Alerts page when the frontend is connected to the backend and the Anthropic API is configured.

**Note:** Running interest cycles requires an Administrator or Branch Manager account.

## Running Tests

Install the project dependencies, then run:

```bash
pytest
```

The test suite is configured to use in-memory/mock implementations of MongoDB and Redis (`mongomock-motor` and `fakeredis`), so external database services should not be required for those tests.

The documented test coverage includes authentication, deposits, withdrawals, transfers, validation, transaction-history filters, cache invalidation, fraud rules, interest calculations, and role checks.

## API Quick Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Register a staff user |
| `POST` | `/auth/login` | Log in and obtain a JWT |
| `GET` | `/auth/me` | Retrieve the current user |
| `POST` | `/accounts` | Create a customer and account |
| `GET` | `/accounts` | List accounts |
| `GET` | `/accounts/{account_no}` | Retrieve an account (Redis-cached) |
| `POST` | `/accounts/{no}/close` | Close an eligible zero-balance account |
| `POST` | `/transactions/deposit` | Deposit funds |
| `POST` | `/transactions/withdraw` | Withdraw funds |
| `POST` | `/transactions/transfer` | Transfer funds between accounts |
| `GET` | `/transactions` | Retrieve transaction history with filters |
| `POST` | `/interest/run` | Run an interest cycle (admin/manager only) |
| `GET` | `/fraud/alerts` | Retrieve transactions flagged by fraud rules |
| `POST` | `/analysis/account` | Generate an AI-assisted risk analysis for recent account activity |

All routes except `/auth/register` and `/auth/login` require an `Authorization: Bearer <token>` header.

## Configuration

Configure environment variables in `.env` based on `.env.example`.

- **Fraud detection:** `FRAUD_LARGE_TXN_AMOUNT`, `FRAUD_VELOCITY_COUNT`, and `FRAUD_VELOCITY_WINDOW_SECONDS` configure the rule thresholds.
- **GenAI analysis:** `ANTHROPIC_API_KEY` enables Claude-powered transaction analysis.
- **Model selection:** `ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5`; change it to a model available to your account.
- **CORS:** The current configuration allows all origins for local development. Restrict allowed origins before deploying publicly.

## Deploy the Frontend with GitHub Pages

GitHub Pages can host the project's **static frontend**. It cannot run the FastAPI backend, MongoDB, or Redis. To use the complete application online, deploy the API and its database/cache services separately, then connect the GitHub Pages frontend to the public API URL.

### 1. Enable GitHub Pages

1. Push this repository to GitHub.
2. Open the repository on GitHub and go to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Add the workflow below as `.github/workflows/deploy-pages.yml`.
5. Commit and push the file to the `main` branch.
6. Open the repository's **Actions** tab and wait for the Pages deployment workflow to complete.
7. Your frontend will be available at `https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPOSITORY_NAME>/`.

### 2. GitHub Actions workflow

Create `.github/workflows/deploy-pages.yml` with:

```yaml
name: Deploy frontend to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: github-pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure GitHub Pages
        uses: actions/configure-pages@v5

      - name: Upload frontend artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: frontend

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

The workflow publishes the contents of `frontend/`, including `BankingSystem.html`. If you want the site to open at the root URL rather than `/BankingSystem.html`, rename the file to `frontend/index.html` and update your project references accordingly.

### 3. Connect the frontend to your backend

GitHub Pages only serves static files. Deploy the FastAPI application to a backend hosting provider that supports Python/Docker, and configure MongoDB and Redis as separately hosted services.

After deployment:

1. Open your GitHub Pages site.
2. Find the **Backend API** card on the Dashboard.
3. Enter your deployed API's HTTPS base URL (not the `/docs` URL).
4. Register or log in and test account and transaction operations.

The backend must allow requests from your GitHub Pages origin through its CORS configuration. Do not leave unrestricted CORS enabled for a public production deployment.

### 4. Required backend configuration

Use `.env.example` as the source of truth for this repository's environment variable names. Configure the required MongoDB, Redis, and authentication/JWT settings in your backend host's environment settings. Add `ANTHROPIC_API_KEY` only if you want Claude-powered transaction analysis.

- Use production database URLs and strong, unique secrets.
- Never commit `.env`, API keys, passwords, or JWT secrets to GitHub.
- Do not use `localhost` database URLs in the deployed backend.
- Ensure the hosted backend can reach MongoDB and Redis.
- Configure `ANTHROPIC_MODEL` to a model available to your Anthropic account.

> **Important:** A successful GitHub Pages deployment makes the frontend publicly accessible; it does not deploy or start the FastAPI backend or provision MongoDB/Redis.

## Future Improvements

- Add stronger production-grade audit logging and security monitoring.
- Expand automated tests for edge cases and failure recovery.
- Add deployment-specific configuration and production security hardening.
