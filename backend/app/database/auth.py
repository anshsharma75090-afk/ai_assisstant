import base64
import hashlib
import hmac
import os
import time
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String

from app.core.config import settings
from app.database.db import Base, SessionLocal, engine


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

security = HTTPBearer()


class AuthRequest(BaseModel):
    name: str | None = None
    email: str
    password: str


def auth_secret():
    return settings.GROQ_API_KEY or settings.GEMINI_API_KEY or "dev-secret-change-me"


def hash_password(password: str, salt: str | None = None):
    active_salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        active_salt.encode("utf-8"),
        120000
    )
    return f"{active_salt}:{base64.urlsafe_b64encode(digest).decode('utf-8')}"


def verify_password(password: str, password_hash: str):
    salt, _ = password_hash.split(":", 1)
    return hmac.compare_digest(hash_password(password, salt), password_hash)


def create_token(user: User):
    expires_at = int(time.time()) + 60 * 60 * 24 * 7
    payload = f"{user.id}:{user.email}:{expires_at}"
    signature = hmac.new(
        auth_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("utf-8")
    return token


def decode_token(token: str):
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        user_id, email, expires_at, signature = decoded.rsplit(":", 3)
        payload = f"{user_id}:{email}:{expires_at}"
        expected_signature = hmac.new(
            auth_secret().encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        if int(expires_at) < int(time.time()):
            raise ValueError("Token expired")

        return int(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        ) from exc


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = decode_token(credentials.credentials)
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def public_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }
