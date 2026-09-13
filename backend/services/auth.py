from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass

from fastapi import Header, HTTPException
from sqlalchemy import select

from backend.database import session_scope
from backend.database.models import UserRecord


TOKEN_TTL_SECONDS = 12 * 60 * 60
PBKDF2_ITERATIONS = 210_000


def _secret() -> bytes:
    return os.getenv("AUTH_SECRET", "hydrosafe-local-dev-secret-change-before-deploy").encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt, expected = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(iterations))
        return hmac.compare_digest(derived, _unb64(expected))
    except Exception:
        return False


def create_token(user: UserRecord) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_unb64(body))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Authentication is required.") from exc


def public_user(user: UserRecord) -> dict:
    return {"id": str(user.id), "name": user.name, "email": user.email}


def get_user_by_email(email: str) -> UserRecord | None:
    with session_scope() as session:
        return session.scalar(select(UserRecord).where(UserRecord.email == email.lower().strip()))


def get_user_by_id(user_id: int) -> UserRecord | None:
    with session_scope() as session:
        return session.get(UserRecord, user_id)


def require_user(authorization: str | None = Header(default=None)) -> UserRecord:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication is required.")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    user = get_user_by_id(int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    return user
