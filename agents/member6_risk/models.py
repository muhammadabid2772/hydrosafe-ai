from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Reading(BaseModel):
    instrument_id: str
    instrument_type: str | None = None
    metric: str
    value: float
    timestamp: datetime | None = None
    previous_value: float | None = None
    previous_timestamp: datetime | None = None
    unit: str | None = None


class QualityInput(BaseModel):
    score: float = Field(ge=0, le=100, description="100 means complete and trustworthy")
    missing_rate: float | None = Field(default=None, ge=0, le=1)
    evidence: str | None = None


class SignalInput(BaseModel):
    instrument_id: str | None = None
    metric: str | None = None
    score: float = Field(ge=0, le=100)
    confidence: float = Field(default=1, ge=0, le=1)
    evidence: str
    scope: Literal["STRUCTURAL", "HYDROMET", "SENSOR_QUALITY"] = "STRUCTURAL"
    source_agent: str | None = None
    observed_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ThresholdInput(BaseModel):
    instrument_id: str
    metric: str
    watch_above: float | None = None
    warning_above: float | None = None
    critical_above: float | None = None
    watch_below: float | None = None
    warning_below: float | None = None
    critical_below: float | None = None
    source: str = Field(description="Engineer-approved source or document reference")


class HydrometContext(BaseModel):
    observed_at: datetime
    reservoir_level_m: float | None = None
    tailwater_level_m: float | None = None
    inflow_m3_s: float | None = None
    outflow_m3_s: float | None = None
    mean_temperature_c: float | None = None
    daily_rainfall_mm: float | None = Field(default=None, ge=0)
    rainfall_7d_mm: float | None = Field(default=None, ge=0)
    reservoir_change_7d_m: float | None = None
    source: str


class RiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    structure: Literal["ACCRD", "POWER_HOUSE", "POWER_INTAKE"]
    readings: list[Reading] = Field(default_factory=list)
    quality: QualityInput | None = None
    trends: list[SignalInput] = Field(default_factory=list)
    anomalies: list[SignalInput] = Field(default_factory=list)
    correlations: list[SignalInput] = Field(default_factory=list)
    thresholds: list[ThresholdInput] = Field(default_factory=list)
    hydromet: HydrometContext | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ContributingFactor(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    evidence: str


class InstrumentRisk(BaseModel):
    instrument_id: str
    metric: str
    score: float
    level: str
    current_value: float
    previous_value: float | None = None
    absolute_change: float | None = None
    change_percent: float | None = None
    rate_per_day: float | None = None
    threshold_exceeded: bool = False
    evidence: list[str]


class AlertEvent(BaseModel):
    alert_id: str
    occurred_at: datetime
    project_id: str
    structure: str
    instrument_id: str
    instrument_type: str | None = None
    metric: str
    unit: str | None = None
    previous_value: float | None = None
    current_value: float
    threshold_value: float
    threshold_direction: Literal["ABOVE", "BELOW"]
    severity: Literal["WATCH", "WARNING", "CRITICAL"]
    threshold_source: str


class HydrometAssessment(BaseModel):
    supplied: bool
    status: Literal["NOT_SUPPLIED", "FRESH", "STALE", "FUTURE_DATED"]
    observed_at: datetime | None = None
    freshness_days: float | None = None
    summary: str
    baseline_deviations: dict[str, float] = Field(default_factory=dict)
    direct_risk_contribution: float = 0
    notes: list[str] = Field(default_factory=list)
    anomaly_signal_count: int = 0
    anomaly_detected: bool = False
    anomaly_severity: Literal["Normal", "Moderate", "High"] | None = None
    anomaly_source: str | None = None
    anomaly_evidence: list[str] = Field(default_factory=list)


class RiskResponse(BaseModel):
    project_id: str
    structure: str
    assessment_status: Literal["ASSESSED", "NOT_ASSESSED"]
    score: float = Field(ge=0, le=100)
    level: Literal["NORMAL", "WATCH", "WARNING", "CRITICAL"]
    warning_message: str
    interpretation: str
    contributing_factors: list[ContributingFactor]
    recommended_next_action: str
    instrument_risks: list[InstrumentRisk]
    alerts: list[AlertEvent]
    active_alert_count: int
    hydromet_assessment: HydrometAssessment
    requires_engineer_review: bool = True
    model_version: str
    assessed_at: datetime
    limitations: list[str]
