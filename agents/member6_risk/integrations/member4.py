from __future__ import annotations

from backend.agents.member4_anomaly.models import Member4AnomalyResponse, Member4CurrentConditions
from backend.agents.member6_risk.models import HydrometContext, SignalInput


def member4_to_signal(result: Member4AnomalyResponse) -> SignalInput:
    score = min(100.0, result.max_abs_z * 25.0) if result.anomaly else 0.0
    drivers = sorted(result.parameters, key=lambda item: item.abs_z, reverse=True)[:2]
    driver_text = ", ".join(f"{item.label} |z|={item.abs_z:.2f}" for item in drivers)
    return SignalInput(
        metric="hydromet_multivariate",
        score=round(score, 2),
        confidence=1.0,
        evidence=(
            f"Member 4 {result.severity.lower()} statistical screen; {driver_text}. "
            "Context only; structural corroboration is required."
        ),
        scope="HYDROMET",
        source_agent=result.source_agent,
        observed_at=result.observed_at,
        details={
            "anomaly": result.anomaly,
            "severity": result.severity,
            "max_abs_z": result.max_abs_z,
            "isolation_forest_flag": result.isolation_forest_flag,
            "model_version": result.model_version,
        },
    )


def member4_to_hydromet_context(
    current: Member4CurrentConditions,
    result: Member4AnomalyResponse,
    source: str,
) -> HydrometContext:
    return HydrometContext(
        observed_at=result.observed_at,
        reservoir_level_m=current.reservoir_level,
        tailwater_level_m=current.tailwater,
        inflow_m3_s=current.inflow,
        mean_temperature_c=current.temperature,
        daily_rainfall_mm=current.rainfall,
        source=source,
    )
