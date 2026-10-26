from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.mongodb import get_db
from app.models.schemas import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate):
    db = get_db()
    if await db.users.find_one({"username": payload.username}):
        raise HTTPException(status_code=409, detail="Username already taken")

    doc = {
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "role": payload.role.value,
    }
    await db.users.insert_one(doc)
    return UserOut(username=doc["username"], full_name=doc["full_name"], role=doc["role"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(username=user["username"], full_name=user["full_name"], role=user["role"])
