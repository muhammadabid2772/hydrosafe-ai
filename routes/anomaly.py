from __future__ import annotations

from fastapi import APIRouter

from backend.agents.member4_anomaly.models import Member4AnomalyRequest, Member4AnomalyResponse
from backend.agents.member4_anomaly.runtime import get_member4_detector


router = APIRouter(prefix="/api/anomaly", tags=["anomaly"])


@router.post("/hydromet/assess", response_model=Member4AnomalyResponse)
def assess_hydromet_anomaly(
    request: Member4AnomalyRequest,
) -> Member4AnomalyResponse:
    return get_member4_detector().assess(request.current, observed_at=request.observed_at)
