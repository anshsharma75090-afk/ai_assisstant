from fastapi import APIRouter, Depends, HTTPException

from app.database.auth import (
    AuthRequest,
    User,
    create_token,
    get_current_user,
    hash_password,
    public_user,
    verify_password,
)
from app.database.db import SessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(request: AuthRequest):
    email = request.email.strip().lower()
    password = request.password.strip()
    name = (request.name or email.split("@")[0]).strip()

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user)
    result = {"token": token, "user": public_user(user)}
    db.close()
    return result


@router.post("/login")
async def login(request: AuthRequest):
    email = request.email.strip().lower()

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(request.password, user.password_hash):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(user)
    result = {"token": token, "user": public_user(user)}
    db.close()
    return result


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"user": public_user(user)}
