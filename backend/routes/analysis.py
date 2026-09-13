from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query

from backend.agents.member1_orchestration.models import UnifiedAnalysisRequest, UnifiedAnalysisResponse
from backend.agents.member1_orchestration.service import build_unified_analysis, load_demo_request
from backend.routes.risk import get_engine


router = APIRouter(prefix="/api/analysis", tags=["unified analysis"])
BACKEND_ROOT = Path(__file__).parents[1]


@lru_cache(maxsize=1)
def _reference_quality() -> dict:
    path = BACKEND_ROOT / "agents" / "member2_validation" / "original" / "member2_validation_report.json"
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/latest", response_model=UnifiedAnalysisResponse)
def latest_analysis(
    project_id: str = Query(default="demo-dam-01", min_length=1),
) -> UnifiedAnalysisResponse:
    request = load_demo_request(BACKEND_ROOT / "datasets" / "structural" / "P01DS1_recent.json")
    request = request.model_copy(update={"project_id": project_id})
    return build_unified_analysis(request, get_engine(), reference_quality=_reference_quality())


@router.post("/run", response_model=UnifiedAnalysisResponse)
def run_analysis(request: UnifiedAnalysisRequest) -> UnifiedAnalysisResponse:
    return build_unified_analysis(request, get_engine())
