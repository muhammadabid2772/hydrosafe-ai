from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agents.member1_orchestration import run_complete_analysis
from backend.routes.anomaly import router as anomaly_router
from backend.routes.risk import router as risk_router


app = FastAPI(
    title="HydroSafe AI API",
    version="0.1.0",
    description="Explainable monitoring-risk integration API. Engineering review remains mandatory.",
)

origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk_router)
app.include_router(anomaly_router)

# Resolves backend/ directory relative to main.py regardless of current working directory
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = str(BASE_DIR / "datasets" / "hydromet" / "member4_hydromet.csv")

latest_analysis_cache: dict[str, Any] = {}


class AuthPayload(BaseModel):
    email: str
    password: str


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hydrosafe-api"}


@app.post("/api/analysis/run", tags=["analysis"])
def run_analysis(file_path: str = DEFAULT_DATASET) -> dict[str, Any]:
    global latest_analysis_cache
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Dataset file not found at {file_path}")

    result = run_complete_analysis(file_path)
    latest_analysis_cache = result
    return result


@app.get("/api/analysis/latest", tags=["analysis"])
def get_latest_analysis() -> dict[str, Any]:
    if not latest_analysis_cache:
        return run_analysis()
    return latest_analysis_cache


@app.post("/api/auth/signup", tags=["auth"])
def signup(payload: AuthPayload) -> dict[str, str]:
    return {"status": "SUCCESS", "message": "User registered successfully", "email": payload.email}


@app.post("/api/auth/login", tags=["auth"])
def login(payload: AuthPayload) -> dict[str, Any]:
    return {
        "status": "SUCCESS",
        "token": "demo-jwt-token-hydrosafe",
        "user": {"email": payload.email, "role": "team_lead"},
    }


@app.get("/api/auth/me", tags=["auth"])
def get_me() -> dict[str, str]:
    return {"email": "admin@hydrosafe.ai", "role": "team_lead"}


@app.post("/api/auth/logout", tags=["auth"])
def logout() -> dict[str, str]:
    return {"status": "SUCCESS", "message": "Logged out successfully"}