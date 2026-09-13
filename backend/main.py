from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database import init_db
from backend.routes.anomaly import router as anomaly_router
from backend.routes.auth import router as auth_router, settings_router
from backend.routes.correlation import router as correlation_router
from backend.routes.reports import router as reports_router
from backend.routes.analysis import router as analysis_router
from backend.routes.risk import router as risk_router


app = FastAPI(
    title="HydroSafe AI API",
    version="0.2.0",
    description="Explainable monitoring-risk integration API. Engineering review remains mandatory.",
)

origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
init_db()
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(reports_router)
app.include_router(correlation_router)
app.include_router(risk_router)
app.include_router(anomaly_router)
app.include_router(analysis_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hydrosafe-api"}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(part) for part in item["loc"] if part != "body"), "message": item["msg"]}
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"message": "Submitted data did not pass validation.", "code": "VALIDATION_FAILED", "errors": errors},
    )
