from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.agents.member2_validation import validate_readings
from backend.agents.member3_trends import analyze_trends
from backend.agents.member4_anomaly.models import Member4CurrentConditions
from backend.agents.member4_anomaly.runtime import get_member4_detector
from backend.agents.member4_anomaly.structural import analyze_structural_anomalies
from backend.agents.member5_correlation import CorrelationEngine
from backend.agents.member6_risk import RiskEngine
from backend.agents.member6_risk.integrations.member4 import member4_to_signal
from backend.agents.member6_risk.models import QualityInput, Reading, RiskRequest, SignalInput

from .models import UnifiedAnalysisRequest, UnifiedAnalysisResponse


def _parse_timestamp(value: Any) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _validated_rows(request: UnifiedAnalysisRequest, validation: dict[str, Any]) -> list[dict[str, Any]]:
    invalid_rows = {int(flag["row"]) for flag in validation.get("flags", [])}
    rows = []
    for index, reading in enumerate(request.readings):
        if index in invalid_rows:
            continue
        raw = reading.model_dump()
        raw["instrument_id"] = str(raw["instrument_id"])
        raw["metric"] = str(raw["metric"])
        raw["value"] = float(raw["value"])
        raw["timestamp"] = _parse_timestamp(raw["timestamp"])
        rows.append(raw)
    return rows


def _trend_payload(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[SignalInput]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["instrument_id"], row["metric"])].append(row)

    series = []
    signals = []
    for (instrument_id, metric), items in sorted(grouped.items()):
        items.sort(key=lambda item: item["timestamp"])
        result = analyze_trends(items)
        item = {
            "instrument_id": instrument_id,
            "instrument_type": items[-1].get("instrument_type"),
            "metric": metric,
            "unit": items[-1].get("unit"),
            **result,
        }
        series.append(item)
        if result["available"]:
            signals.append(SignalInput(
                instrument_id=instrument_id,
                metric=metric,
                score=result["score"],
                confidence=result["confidence"],
                evidence=result["evidence"],
                scope="STRUCTURAL",
                source_agent="member3_trends",
                observed_at=items[-1]["timestamp"],
                details={key: value for key, value in result.items() if key != "chart_points"},
            ))

    ready_count = sum(bool(item["available"]) for item in series)
    return {
        "available": ready_count > 0,
        "status": "READY" if ready_count == len(series) and ready_count else "PARTIAL" if ready_count else "UNAVAILABLE",
        "agent": "member3_trends",
        "series_count": len(series),
        "ready_series_count": ready_count,
        "series": series,
        "message": None if ready_count else "No instrument series contained at least two validated observations.",
    }, signals




def _automatic_hydromet_signal(request: UnifiedAnalysisRequest) -> SignalInput | None:
    context = request.hydromet
    if context is None:
        return None
    required = [
        context.reservoir_level_m,
        context.tailwater_level_m,
        context.inflow_m3_s,
        context.daily_rainfall_mm,
        context.mean_temperature_c,
    ]
    if any(value is None for value in required):
        return None
    current = Member4CurrentConditions(
        reservoir_level=context.reservoir_level_m,
        tailwater=context.tailwater_level_m,
        inflow=context.inflow_m3_s,
        rainfall=context.daily_rainfall_mm,
        temperature=context.mean_temperature_c,
    )
    result = get_member4_detector().assess(current, observed_at=context.observed_at)
    return member4_to_signal(result)


def _risk_readings(rows: list[dict[str, Any]]) -> list[Reading]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["instrument_id"], row["metric"])].append(row)
    result = []
    for items in grouped.values():
        items.sort(key=lambda item: item["timestamp"])
        current = items[-1]
        previous = items[-2] if len(items) > 1 else None
        result.append(Reading(
            instrument_id=current["instrument_id"],
            instrument_type=current.get("instrument_type"),
            metric=current["metric"],
            value=current["value"],
            timestamp=current["timestamp"],
            previous_value=previous["value"] if previous else None,
            previous_timestamp=previous["timestamp"] if previous else None,
            unit=current.get("unit"),
        ))
    return result


def build_unified_analysis(
    request: UnifiedAnalysisRequest,
    engine: RiskEngine,
    reference_quality: dict[str, Any] | None = None,
) -> UnifiedAnalysisResponse:
    validation = validate_readings(request.readings)
    rows = _validated_rows(request, validation) if validation["available"] else []
    trends, trend_signals = _trend_payload(rows)

    structural_anomaly_summary, generated_structural_anomalies = analyze_structural_anomalies(rows)
    hydromet_signal = _automatic_hydromet_signal(request)
    generated_anomalies = [*generated_structural_anomalies]
    if hydromet_signal is not None:
        generated_anomalies.append(hydromet_signal)
    all_anomaly_signals = [*request.anomalies, *generated_anomalies]

    correlation_result, generated_correlations = CorrelationEngine().analyze(
        rows=rows,
        trends=trend_signals,
        anomalies=all_anomaly_signals,
    )
    all_correlation_signals = [*request.correlations, *generated_correlations]

    quality_evidence = (
        f"Validation accepted {validation['valid_count']} of {validation['total_records']} structural readings; "
        f"quality {validation['score']:.1f}/100."
        if validation["available"] else validation["warning"]
    )
    risk_quality = QualityInput(
        score=validation["score"],
        missing_rate=(validation["flagged_count"] / validation["total_records"]) if validation["total_records"] else None,
        evidence=quality_evidence,
    ) if validation["available"] else None

    risk_request = RiskRequest(
        project_id=request.project_id,
        structure=request.structure,
        readings=_risk_readings(rows),
        quality=risk_quality,
        trends=trend_signals,
        anomalies=all_anomaly_signals,
        correlations=all_correlation_signals,
        thresholds=request.thresholds,
        hydromet=request.hydromet,
        context={"data_mode": request.data_mode, "source": request.source},
    )
    risk = engine.assess(risk_request)
    observed_at = max((row["timestamp"] for row in rows), default=None)
    if request.data_mode == "HISTORICAL_REPLAY":
        risk = risk.model_copy(update={
            "interpretation": f"Historical replay only. {risk.interpretation}",
            "limitations": ["This response uses historical observations and is not live telemetry.", *risk.limitations],
        })

    quality = dict(validation)
    quality["flags"] = validation.get("flags", [])[:25]
    quality["flags_truncated"] = len(validation.get("flags", [])) > 25
    if reference_quality:
        quality["reference_dataset"] = {
            key: value for key, value in reference_quality.items()
            if key not in {"flags"}
        }

    identity = json.dumps({
        "project_id": request.project_id,
        "structure": request.structure,
        "source": request.source,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "records": len(rows),
    }, sort_keys=True)
    analysis_id = "analysis-" + hashlib.sha256(identity.encode()).hexdigest()[:16]
    partial = not validation["available"] or not trends["available"]

    anomaly_payload = [item.model_dump(mode="json") for item in all_anomaly_signals]
    correlation_payload = [item.model_dump(mode="json") for item in correlation_result.evidence]
    for item in request.correlations:
        correlation_payload.append({
            "evidence_type": "EXTERNAL_SIGNAL",
            "correlation_detected": item.score >= 50,
            "confidence": item.confidence,
            "score": item.score,
            "related_parameters": [value for value in [item.instrument_id, item.metric] if value],
            "explanation": item.evidence,
            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
            "details": item.details,
        })

    return UnifiedAnalysisResponse(
        analysis_id=analysis_id,
        project_id=request.project_id,
        structure=request.structure,
        generated_at=risk.assessed_at,
        data_mode=request.data_mode,
        source=request.source,
        source_observed_at=observed_at,
        quality=quality,
        trends=trends,
        anomalies=anomaly_payload,
        correlations=correlation_payload,
        risk=risk,
        report={
            "status": "PARTIAL" if partial else "READY",
            "validation_applied": validation["available"],
            "trend_analysis_applied": trends["available"],
            "anomaly_analysis": structural_anomaly_summary,
            "member4_structural_applied": structural_anomaly_summary["available"],
            "member4_hydromet_applied": hydromet_signal is not None,
            "member5_correlation_status": correlation_result.status,
            "member5_detected_count": correlation_result.detected_count,
            "risk_assessment_status": risk.assessment_status,
            "member4_required": False,
            "message": (
                "Unified analysis now generates Member 4 structural anomaly evidence and Member 5 correlation evidence automatically. "
                "Hydrometeorological screening remains contextual until structural evidence corroborates it."
            ),
        },
    )


def load_demo_request(dataset_path: Path) -> UnifiedAnalysisRequest:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    return UnifiedAnalysisRequest(
        project_id="demo-dam-01",
        structure=payload["structure"],
        readings=payload["readings"][-10:],
        data_mode="HISTORICAL_REPLAY",
        source="Validated ACCRD piezometer monitoring dataset",
    )
