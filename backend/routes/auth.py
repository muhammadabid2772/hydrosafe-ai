from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from backend.database import session_scope
from backend.database.models import UserRecord
from backend.services.auth import create_token, hash_password, public_user, require_user, verify_password


router = APIRouter(prefix="/api/auth", tags=["authentication"])
settings_router = APIRouter(prefix="/api/settings", tags=["settings"])


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)


class PasswordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


def auth_response(user: UserRecord) -> dict:
    return {"user": public_user(user), "access_token": create_token(user), "token_type": "bearer"}


@router.post("/signup")
def signup(request: SignupRequest) -> dict:
    email = request.email.lower().strip()
    with session_scope() as session:
        if session.scalar(select(UserRecord).where(UserRecord.email == email)):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = UserRecord(name=request.name.strip(), email=email, password_hash=hash_password(request.password))
        session.add(user)
        session.flush()
        result = auth_response(user)
    return result


@router.post("/login")
def login(request: LoginRequest) -> dict:
    email = request.email.lower().strip()
    with session_scope() as session:
        user = session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return auth_response(user)


@router.get("/me")
def me(user: UserRecord = Depends(require_user)) -> dict:
    return public_user(user)


@router.post("/logout")
def logout(_: UserRecord = Depends(require_user)) -> dict:
    return {"status": "ok"}


@settings_router.put("/profile")
def update_profile(request: ProfileUpdate, user: UserRecord = Depends(require_user)) -> dict:
    with session_scope() as session:
        stored = session.get(UserRecord, user.id)
        stored.name = request.name.strip()
        stored.updated_at = datetime.now(timezone.utc)
        session.flush()
        return {"user": public_user(stored)}


@settings_router.put("/password")
def update_password(request: PasswordUpdate, user: UserRecord = Depends(require_user)) -> dict:
    if request.current_password == request.new_password:
        raise HTTPException(status_code=400, detail="Choose a new password that is different from the current password.")
    with session_scope() as session:
        stored = session.get(UserRecord, user.id)
        if not verify_password(request.current_password, stored.password_hash):
            raise HTTPException(status_code=400, detail="The current password is incorrect.")
        stored.password_hash = hash_password(request.new_password)
        stored.updated_at = datetime.now(timezone.utc)
    return {"status": "ok", "message": "Password changed successfully."}
