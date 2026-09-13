from __future__ import annotations

import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from backend.agents.member4_anomaly.models import Member4AnomalyResponse, Member4CurrentConditions
from backend.agents.member4_anomaly.runtime import get_member4_detector
from backend.agents.member6_risk import RiskEngine, RiskRequest, RiskResponse
from backend.agents.member6_risk.integrations.member4 import member4_to_hydromet_context, member4_to_signal


router = APIRouter(prefix="/api/risk", tags=["risk"])


class RiskWithMember4Request(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk: RiskRequest
    current_hydromet: Member4CurrentConditions
    observed_at: datetime
    source: str = "Member 4 hydrometeorological anomaly detector"


class RiskWithMember4Response(BaseModel):
    anomaly: Member4AnomalyResponse
    risk: RiskResponse


@lru_cache(maxsize=1)
def get_engine() -> RiskEngine:
    default = Path(__file__).parents[1] / "agents" / "member6_risk" / "artifacts" / "baseline.json"
    hydromet_default = Path(__file__).parents[1] / "agents" / "member6_risk" / "artifacts" / "hydromet_baseline.json"
    return RiskEngine(
        os.getenv("RISK_BASELINE_PATH", str(default)),
        hydromet_baseline_path=os.getenv("RISK_HYDROMET_BASELINE_PATH", str(hydromet_default)),
    )


@router.post("/assess", response_model=RiskResponse)
def assess_risk(request: RiskRequest) -> RiskResponse:
    return get_engine().assess(request)


@router.post("/assess-with-member4", response_model=RiskWithMember4Response)
def assess_risk_with_member4(request: RiskWithMember4Request) -> RiskWithMember4Response:
    anomaly = get_member4_detector().assess(request.current_hydromet, observed_at=request.observed_at)
    member4_signal = member4_to_signal(anomaly)
    other_anomalies = [
        signal
        for signal in request.risk.anomalies
        if not (signal.scope == "HYDROMET" and signal.source_agent == "member4_anomaly")
    ]
    hydromet = request.risk.hydromet or member4_to_hydromet_context(
        request.current_hydromet,
        anomaly,
        request.source,
    )
    risk_request = request.risk.model_copy(
        update={"anomalies": [*other_anomalies, member4_signal], "hydromet": hydromet}
    )
    return RiskWithMember4Response(anomaly=anomaly, risk=get_engine().assess(risk_request))
