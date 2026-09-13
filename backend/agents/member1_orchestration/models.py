from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.member6_risk.models import (
    HydrometContext,
    RiskResponse,
    SignalInput,
    ThresholdInput,
)


class RawReading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str | None = None
    instrument_type: str | None = None
    metric: str | None = None
    value: Any = None
    timestamp: Any = None
    unit: str | None = None


class UnifiedAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    structure: Literal["ACCRD", "POWER_HOUSE", "POWER_INTAKE"]
    readings: list[RawReading] = Field(default_factory=list)
    thresholds: list[ThresholdInput] = Field(default_factory=list)
    anomalies: list[SignalInput] = Field(default_factory=list)
    correlations: list[SignalInput] = Field(default_factory=list)
    hydromet: HydrometContext | None = None
    data_mode: Literal["LIVE", "HISTORICAL_REPLAY", "OPERATOR_INPUT"] = "OPERATOR_INPUT"
    source: str = "Unified API input"


class UnifiedAnalysisResponse(BaseModel):
    analysis_id: str
    project_id: str
    structure: str
    generated_at: datetime
    data_mode: Literal["LIVE", "HISTORICAL_REPLAY", "OPERATOR_INPUT"]
    source: str
    source_observed_at: datetime | None = None
    quality: dict[str, Any]
    trends: dict[str, Any]
    anomalies: list[dict[str, Any]]
    correlations: list[dict[str, Any]]
    risk: RiskResponse
    report: dict[str, Any]
