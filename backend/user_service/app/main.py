"""User service with bcrypt auth and JWT token issuing."""

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# FastAPI application for user management.
app = FastAPI(title="User Service")

# Password hasher context.
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings for beta mode (can be overridden by environment variables).
JWT_SECRET = os.getenv("JWT_SECRET", "beta-secret-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))

# In-memory users storage for beta demo.
users: dict[str, dict] = {}


class User(BaseModel):
    """Input DTO for registration and login endpoints."""

    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Почта пользователя")
    password: str = Field(min_length=8, max_length=256, description="Пароль пользователя")


@app.get("/health")
def healthcheck():
    """Basic liveness endpoint with auth mode info."""
    return {"status": "ok", "auth_mode": "bcrypt+jwt"}


@app.post("/register")
def register(user: User):
    """Register user with duplicate check and password hashing."""
    if user.email in users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user already exists")

    users[user.email] = {
        "password_hash": pwd.hash(user.password[:72]),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login_at": None,
    }
    return {"status": "registered", "email": user.email}


def _b64url_encode(data: bytes) -> str:
    """Base64-url encode helper without trailing '='."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _create_access_token(email: str) -> tuple[str, int]:
    """Create JWT token for authenticated user (HS256)."""
    if JWT_ALGORITHM != "HS256":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="unsupported jwt algorithm")

    expires_delta = timedelta(minutes=JWT_EXPIRES_MINUTES)
    now = datetime.now(timezone.utc)
    exp = now + expires_delta

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": email,
        "scope": "user",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    token = f"{header_b64}.{payload_b64}.{signature_b64}"
    return token, JWT_EXPIRES_MINUTES * 60


@app.post("/login")
def login(user: User):
    """Validate user credentials via bcrypt and return JWT access token."""
    user_data = users.get(user.email)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    if not pwd.verify(user.password[:72], user_data["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    user_data["last_login_at"] = datetime.now(timezone.utc).isoformat()
    access_token, expires_in = _create_access_token(user.email)
    return {
        "status": "authorized",
        "email": user.email,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@app.get("/users")
def get_users():
    """Return a safe view of users list (without password hashes)."""
    return [
        {
            "email": email,
            "created_at": data["created_at"],
            "last_login_at": data["last_login_at"],
        }
        for email, data in users.items()
    ]
