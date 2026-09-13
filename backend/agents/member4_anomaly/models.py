from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Member4CurrentConditions(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    reservoir_level: float
    tailwater: float
    inflow: float = Field(ge=0)
    rainfall: float = Field(ge=0)
    temperature: float


class Member4AnomalyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current: Member4CurrentConditions
    observed_at: datetime


class Member4ParameterAssessment(BaseModel):
    metric: str
    label: str
    value: float
    unit: str
    historical_mean: float
    historical_std: float
    historical_min: float
    historical_max: float
    abs_z: float
    flagged: bool


class Member4HistoryQuality(BaseModel):
    raw_rows: int
    complete_rows: int
    date_start: str | None = None
    date_end: str | None = None
    missing_by_parameter: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class Member4AnomalyResponse(BaseModel):
    source_agent: Literal["member4_anomaly"] = "member4_anomaly"
    scope: Literal["HYDROMET"] = "HYDROMET"
    model_version: str
    observed_at: datetime
    anomaly: bool
    severity: Literal["Normal", "Moderate", "High"]
    max_abs_z: float
    isolation_forest_flag: bool
    isolation_forest_score: float
    contamination: float
    parameters: list[Member4ParameterAssessment]
    history_quality: Member4HistoryQuality
    engineering_interpretation: str
    direct_structural_risk_contribution: Literal[0] = 0
    limitations: list[str]
