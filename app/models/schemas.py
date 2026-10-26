from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth / Users ----------

class UserRole(str, Enum):
    administrator = "Administrator"
    branch_manager = "Branch Manager"
    teller = "Teller"
    auditor = "Auditor"


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole = UserRole.teller


class UserOut(BaseModel):
    username: str
    full_name: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Customers & Accounts ----------

class AccountType(str, Enum):
    savings = "Savings"
    current = "Current"


class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str


class AccountCreate(BaseModel):
    customer: CustomerCreate
    account_type: AccountType = AccountType.savings
    opening_deposit: float = Field(ge=0, default=0)


class AccountOut(BaseModel):
    account_no: int
    customer_id: str
    customer_name: str
    account_type: str
    balance: float
    status: str
    created_at: datetime


# ---------- Transactions ----------

class TxnType(str, Enum):
    deposit = "Deposit"
    withdrawal = "Withdrawal"
    transfer = "Transfer"


class DepositRequest(BaseModel):
    account_no: int
    amount: float = Field(gt=0)
    note: Optional[str] = None


class WithdrawalRequest(BaseModel):
    account_no: int
    amount: float = Field(gt=0)
    note: Optional[str] = None


class TransferRequest(BaseModel):
    from_account_no: int
    to_account_no: int
    amount: float = Field(gt=0)
    note: Optional[str] = None


class TransactionOut(BaseModel):
    txn_id: int
    account_no: int
    counterparty_account_no: Optional[int] = None
    type: str
    amount: float
    balance_after: float
    status: str
    fraud_flags: list[str] = []
    created_at: datetime


# ---------- Interest ----------

class InterestRunRequest(BaseModel):
    annual_rate_percent: float = Field(gt=0, default=4.0)
    period_years: float = Field(gt=0, default=1 / 12)


# ---------- GenAI analysis ----------

class TransactionAnalysisRequest(BaseModel):
    account_no: Optional[int] = None
    txn_id: Optional[int] = None
    lookback: int = 25
