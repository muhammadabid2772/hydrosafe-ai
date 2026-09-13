from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from backend.agents.member1_orchestration.models import UnifiedAnalysisResponse
from backend.database import session_scope
from backend.database.models import ReportRecord, UserRecord
from backend.services.auth import require_user
from backend.services.reporting import generate_report


router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis: UnifiedAnalysisResponse


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def serialize(record: ReportRecord) -> dict:
    return {
        "report_id": record.report_id,
        "project_id": record.project_id,
        "structure": record.structure,
        "analysis_id": record.analysis_id,
        "risk_level": record.risk_level,
        "risk_score": float(record.risk_score),
        "title": record.title,
        "content": record.content,
        "ai_enhanced": record.ai_enhanced == "true",
        "created_at": _iso(record.created_at),
    }


@router.post("/generate")
def create_report(request: ReportGenerateRequest, user: UserRecord = Depends(require_user)) -> dict:
    generated = generate_report(request.analysis)
    stamp = datetime.now(timezone.utc).isoformat()
    report_id = "report-" + hashlib.sha256(f"{request.analysis.analysis_id}|{user.id}|{stamp}".encode()).hexdigest()[:16]
    with session_scope() as session:
        record = ReportRecord(
            report_id=report_id,
            user_id=user.id,
            project_id=request.analysis.project_id,
            structure=request.analysis.structure,
            analysis_id=request.analysis.analysis_id,
            risk_level=request.analysis.risk.level,
            risk_score=str(request.analysis.risk.score),
            title=generated.title,
            content=generated.content,
            ai_enhanced="true" if generated.ai_enhanced else "false",
        )
        session.add(record)
        session.flush()
        payload = serialize(record)
        payload["provider_status"] = generated.provider_status
        return payload


@router.get("")
def list_reports(user: UserRecord = Depends(require_user)) -> list[dict]:
    with session_scope() as session:
        records = session.scalars(
            select(ReportRecord).where(ReportRecord.user_id == user.id).order_by(ReportRecord.created_at.desc()).limit(25)
        ).all()
        return [serialize(record) for record in records]
