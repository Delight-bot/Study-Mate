from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import execute_query, execute_update

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    email: str | None = None
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    existing = await execute_query("SELECT id FROM users WHERE username = ?", (req.username,))
    if existing:
        raise HTTPException(status_code=409, detail="That username is already taken")

    user_id = await execute_update(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (req.username, req.email, hash_password(req.password)),
    )
    token = create_access_token(user_id, req.username)
    return {"token": token, "user_id": user_id, "username": req.username}


@router.post("/login")
async def login(req: LoginRequest):
    rows = await execute_query(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (req.username,),
    )
    if not rows or not rows[0]["password_hash"] or not verify_password(req.password, rows[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user = rows[0]
    token = create_access_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
