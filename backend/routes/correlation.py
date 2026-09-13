from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.agents.member2_validation import validate_readings
from backend.agents.member5_correlation import CorrelationEngine
from backend.agents.member6_risk.models import SignalInput


router = APIRouter(prefix="/api/correlation", tags=["correlation"])


class CorrelationReading(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instrument_id: str
    instrument_type: str | None = None
    metric: str
    value: float
    timestamp: datetime
    unit: str | None = None


class CorrelationAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    readings: list[CorrelationReading] = Field(default_factory=list)
    trends: list[SignalInput] = Field(default_factory=list)
    anomalies: list[SignalInput] = Field(default_factory=list)


@router.post("/analyze")
def analyze_correlations(request: CorrelationAnalyzeRequest) -> dict[str, Any]:
    raw = [item.model_dump() for item in request.readings]
    validation = validate_readings(raw)
    invalid_rows = {int(flag["row"]) for flag in validation.get("flags", [])}
    rows = []
    for index, reading in enumerate(request.readings):
        if index in invalid_rows:
            continue
        row = reading.model_dump()
        timestamp = row["timestamp"]
        row["timestamp"] = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc)
        rows.append(row)
    result, signals = CorrelationEngine().analyze(rows, request.trends, request.anomalies)
    payload = result.model_dump(mode="json")
    payload["risk_signals"] = [item.model_dump(mode="json") for item in signals]
    payload["validation"] = validation
    return payload
