from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .baseline import MODEL_VERSION, load_baselines
from .config import RiskConfig
from .models import (
    AlertEvent, ContributingFactor, HydrometAssessment, InstrumentRisk, Reading,
    RiskRequest, RiskResponse, SignalInput, ThresholdInput,
)


LABELS = {
    "data_quality": "Data quality", "baseline_deviation": "Historical baseline deviation",
    "trend": "Trend escalation", "anomaly": "Anomaly evidence", "correlation": "Cross-sensor inconsistency",
}


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _signal_score(signals: list[SignalInput]) -> tuple[float, str]:
    if not signals:
        return 0.0, "No upstream signal supplied."
    adjusted = sorted((_clamp(signal.score * signal.confidence), signal.evidence) for signal in signals)
    top = adjusted[-3:]
    score = 0.65 * top[-1][0] + 0.35 * (sum(value for value, _ in top) / len(top))
    return _clamp(score), "; ".join(evidence for _, evidence in reversed(top))


def _z_to_score(z_score: float) -> float:
    z_score = abs(z_score)
    if z_score <= 2:
        return z_score * 8
    if z_score <= 3:
        return 16 + (z_score - 2) * 24
    if z_score <= 5:
        return 40 + (z_score - 3) * 20
    return min(100, 80 + (z_score - 5) * 5)


def _threshold_score(reading: Reading, threshold: ThresholdInput) -> tuple[float, str, float, str, str] | None:
    checks = (
        (threshold.critical_above, lambda value: reading.value >= value, 100, "critical high", "ABOVE", "CRITICAL"),
        (threshold.critical_below, lambda value: reading.value <= value, 100, "critical low", "BELOW", "CRITICAL"),
        (threshold.warning_above, lambda value: reading.value >= value, 70, "warning high", "ABOVE", "WARNING"),
        (threshold.warning_below, lambda value: reading.value <= value, 70, "warning low", "BELOW", "WARNING"),
        (threshold.watch_above, lambda value: reading.value >= value, 40, "watch high", "ABOVE", "WATCH"),
        (threshold.watch_below, lambda value: reading.value <= value, 40, "watch low", "BELOW", "WATCH"),
    )
    for limit, comparator, score, label, direction, severity in checks:
        if limit is not None and comparator(limit):
            return float(score), f"{label} threshold {limit:g} crossed; source: {threshold.source}", limit, direction, severity
    return None


class RiskEngine:
    def __init__(
        self,
        baseline_path: str | Path | None = None,
        config: RiskConfig | None = None,
        hydromet_baseline_path: str | Path | None = None,
    ):
        self.config = config or RiskConfig()
        self.baselines = {"profiles": {}, "model_version": MODEL_VERSION}
        if baseline_path and Path(baseline_path).exists():
            self.baselines = load_baselines(baseline_path)
        self.hydromet_baseline = {"monthly_profiles": {}}
        if hydromet_baseline_path and Path(hydromet_baseline_path).exists():
            self.hydromet_baseline = json.loads(Path(hydromet_baseline_path).read_text(encoding="utf-8"))

    def _assess_hydromet(
        self,
        request: RiskRequest,
        assessed_at: datetime,
        anomaly_signals: list[SignalInput],
    ) -> HydrometAssessment:
        context = request.hydromet
        anomaly_detected = any(bool(signal.details.get("anomaly", signal.score > 0)) for signal in anomaly_signals)
        severities = {signal.details.get("severity") for signal in anomaly_signals}
        anomaly_severity = next(
            (level for level in ("High", "Moderate", "Normal") if level in severities),
            None,
        )
        anomaly_evidence = [signal.evidence for signal in anomaly_signals]
        anomaly_source = next((signal.source_agent for signal in anomaly_signals if signal.source_agent), None)
        if context is None:
            return HydrometAssessment(
                supplied=False,
                status="NOT_SUPPLIED",
                summary=(
                    "No raw hydrometeorological context was supplied; a statistical screening signal was supplied."
                    if anomaly_signals else "No hydrometeorological context was supplied."
                ),
                notes=["Absence of optional context does not create a risk score."],
                anomaly_signal_count=len(anomaly_signals), anomaly_detected=anomaly_detected,
                anomaly_severity=anomaly_severity, anomaly_source=anomaly_source,
                anomaly_evidence=anomaly_evidence,
            )
        observed_at = context.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age_days = (assessed_at - observed_at).total_seconds() / 86400
        if age_days < -1:
            status = "FUTURE_DATED"
        elif age_days > 2:
            status = "STALE"
        else:
            status = "FRESH"
        reported_age_days = max(age_days, 0.0) if status == "FRESH" else age_days
        fields = (
            "reservoir_level_m", "tailwater_level_m", "inflow_m3_s", "outflow_m3_s",
            "mean_temperature_c", "daily_rainfall_mm",
        )
        deviations: dict[str, float] = {}
        profiles = self.hydromet_baseline.get("monthly_profiles", {})
        for field in fields:
            value = getattr(context, field)
            profile = profiles.get(f"{observed_at.month:02d}|{field}")
            if value is not None and profile and profile.get("robust_scale", 0) > 0:
                deviations[field] = round((value - profile["median"]) / profile["robust_scale"], 3)
        details = []
        if context.reservoir_level_m is not None:
            details.append(f"reservoir {context.reservoir_level_m:g} m")
        if context.rainfall_7d_mm is not None:
            details.append(f"7-day rainfall {context.rainfall_7d_mm:g} mm")
        elif context.daily_rainfall_mm is not None:
            details.append(f"daily rainfall {context.daily_rainfall_mm:g} mm")
        if context.inflow_m3_s is not None:
            details.append(f"inflow {context.inflow_m3_s:g} m³/s")
        summary = f"Hydromet context is {status.lower()}: " + (", ".join(details) or "no core values supplied") + "."
        notes = [
            "Hydromet values are contextual evidence and contribute 0 points directly to structural risk.",
            "Member 5 should compare sensor response with these drivers and send the result as correlation evidence.",
        ]
        if anomaly_signals:
            notes.append(
                "Member 4 statistical anomalies are recorded as hydromet context and do not enter the structural anomaly score."
            )
        if status != "FRESH":
            notes.append("Do not use this context for a current operational decision until its timestamp is verified or refreshed.")
        return HydrometAssessment(
            supplied=True, status=status, observed_at=observed_at,
            freshness_days=round(reported_age_days, 3), summary=summary,
            baseline_deviations=deviations, direct_risk_contribution=0, notes=notes,
            anomaly_signal_count=len(anomaly_signals), anomaly_detected=anomaly_detected,
            anomaly_severity=anomaly_severity, anomaly_source=anomaly_source,
            anomaly_evidence=anomaly_evidence,
        )

    def _reading_risk(
        self, project_id: str, structure: str, reading: Reading, thresholds: list[ThresholdInput], assessed_at: datetime
    ) -> tuple[InstrumentRisk, AlertEvent | None]:
        matching = [item for item in thresholds if item.instrument_id == reading.instrument_id and item.metric == reading.metric]
        evidence: list[str] = []
        threshold_risk = 0.0
        threshold_hit: tuple[float, str, float, str, str] | None = None
        for threshold in matching:
            result = _threshold_score(reading, threshold)
            if result and result[0] > threshold_risk:
                threshold_risk, explanation = result[0], result[1]
                threshold_hit = result
                evidence = [explanation]
        profiles = self.baselines.get("profiles", {})
        key = f"{structure}|{reading.instrument_id}|{reading.metric}"
        profile = profiles.get(key)
        if profile is None:
            candidates = [
                value for value in profiles.values()
                if value["structure"] == structure and value["instrument_id"] == reading.instrument_id
            ]
            if len(candidates) == 1:
                profile = candidates[0]
        baseline_risk = 0.0
        if profile:
            z_score = (reading.value - profile["median"]) / profile["robust_scale"]
            baseline_risk = _z_to_score(z_score)
            evidence.append(
                f"value {reading.value:g} vs historical median {profile['median']:.4g} "
                f"({z_score:+.2f} robust SD, n={profile['count']})"
            )
        else:
            evidence.append("No matching historical profile; baseline contribution unavailable.")
        score = max(threshold_risk, baseline_risk)
        absolute_change = reading.value - reading.previous_value if reading.previous_value is not None else None
        change_percent = None
        if absolute_change is not None and reading.previous_value not in (None, 0):
            change_percent = absolute_change / abs(reading.previous_value) * 100
        rate_per_day = None
        if absolute_change is not None and reading.timestamp and reading.previous_timestamp:
            elapsed_days = (reading.timestamp - reading.previous_timestamp).total_seconds() / 86400
            if elapsed_days > 0:
                rate_per_day = absolute_change / elapsed_days
        instrument_risk = InstrumentRisk(
            instrument_id=reading.instrument_id, metric=reading.metric, score=round(_clamp(score), 2),
            level=self.config.level_for(score), current_value=reading.value, previous_value=reading.previous_value,
            absolute_change=round(absolute_change, 6) if absolute_change is not None else None,
            change_percent=round(change_percent, 3) if change_percent is not None else None,
            rate_per_day=round(rate_per_day, 6) if rate_per_day is not None else None,
            threshold_exceeded=threshold_hit is not None, evidence=evidence,
        )
        alert = None
        if threshold_hit:
            _, _, limit, direction, severity = threshold_hit
            threshold = next(item for item in matching if _threshold_score(reading, item) == threshold_hit)
            identity = f"{project_id}|{structure}|{reading.instrument_id}|{reading.metric}|{reading.timestamp}|{limit}|{severity}"
            alert = AlertEvent(
                alert_id=hashlib.sha256(identity.encode()).hexdigest()[:20],
                occurred_at=reading.timestamp or assessed_at, project_id=project_id, structure=structure,
                instrument_id=reading.instrument_id, instrument_type=reading.instrument_type, metric=reading.metric,
                unit=reading.unit, previous_value=reading.previous_value, current_value=reading.value,
                threshold_value=limit, threshold_direction=direction, severity=severity,
                threshold_source=threshold.source,
            )
        return instrument_risk, alert

    def assess(self, request: RiskRequest) -> RiskResponse:
        assessed_at = datetime.now(timezone.utc)
        hydromet_anomalies = [signal for signal in request.anomalies if signal.scope == "HYDROMET"]
        structural_anomalies = [signal for signal in request.anomalies if signal.scope != "HYDROMET"]
        hydromet_assessment = self._assess_hydromet(request, assessed_at, hydromet_anomalies)
        assessed = [
            self._reading_risk(request.project_id, request.structure, reading, request.thresholds, assessed_at)
            for reading in request.readings
        ]
        instrument_risks = [item[0] for item in assessed]
        alerts = [item[1] for item in assessed if item[1] is not None]
        baseline_score = max((risk.score for risk in instrument_risks), default=0.0)
        baseline_evidence = (
            max(instrument_risks, key=lambda item: item.score).evidence[0]
            if instrument_risks else "No current readings supplied."
        )
        if request.quality:
            quality_score = _clamp(100 - request.quality.score)
            quality_evidence = request.quality.evidence or f"Upstream quality score is {request.quality.score:.1f}/100."
        else:
            quality_score = 25.0
            quality_evidence = "Quality agent output missing; conservative 25/100 uncertainty applied."
        trend_score, trend_evidence = _signal_score(request.trends)
        anomaly_score, anomaly_evidence = _signal_score(structural_anomalies)
        correlation_score, correlation_evidence = _signal_score(request.correlations)
        values = {
            "data_quality": (quality_score, quality_evidence),
            "baseline_deviation": (baseline_score, baseline_evidence),
            "trend": (trend_score, trend_evidence),
            "anomaly": (anomaly_score, anomaly_evidence),
            "correlation": (correlation_score, correlation_evidence),
        }
        weighted_mean = sum(values[key][0] * weight for key, weight in self.config.weights.items())
        strongest = max(score for score, _ in values.values())
        score = _clamp(max(weighted_mean, strongest * self.config.strongest_factor_floor))
        level = self.config.level_for(score)
        structural_evidence_supplied = bool(
            request.readings or request.trends or structural_anomalies or request.correlations
        )
        assessment_status = "ASSESSED" if structural_evidence_supplied else "NOT_ASSESSED"
        factors = [
            ContributingFactor(key=key, label=LABELS[key], score=round(values[key][0], 2), weight=weight, evidence=values[key][1])
            for key, weight in self.config.weights.items()
        ]
        factors.sort(key=lambda factor: factor.score * factor.weight, reverse=True)
        message = {
            "NORMAL": "No material risk escalation detected in the supplied evidence.",
            "WATCH": "A developing condition needs closer review and increased monitoring.",
            "WARNING": "Multiple or strong indicators require prompt engineering review.",
            "CRITICAL": "Critical evidence detected. Follow the approved emergency and escalation procedure now.",
        }[level]
        action = {
            "NORMAL": "Continue the approved monitoring schedule and verify new data at ingestion.",
            "WATCH": "Validate the leading instrument, compare nearby instruments and reservoir level, then increase review frequency.",
            "WARNING": "Notify the responsible dam-safety engineer, verify readings in the field, and apply the approved action-level procedure.",
            "CRITICAL": "Escalate immediately under the site's Emergency Action Plan; do not rely on this software as the decision authority.",
        }[level]
        if assessment_status == "NOT_ASSESSED":
            message = "Structural risk has not been assessed because no validated structural evidence was supplied."
            action = "Obtain validated structural readings and upstream agent evidence before assigning a structural risk state."
        leading = factors[0]
        alert_sentence = (
            f" {len(alerts)} approved threshold alert{'s' if len(alerts) != 1 else ''} are active."
            if alerts else " No approved threshold was exceeded."
        )
        interpretation = (
            f"{request.structure} structural risk is not assessed. "
            f"No structural readings, trends, anomalies or correlations were supplied. {hydromet_assessment.summary}"
            if assessment_status == "NOT_ASSESSED"
            else (
                f"{request.structure} is assessed as {level} at {score:.1f}/100. "
                f"The leading factor is {leading.label.lower()}: {leading.evidence}{alert_sentence} "
                f"{hydromet_assessment.summary}"
            )
        )
        if hydromet_anomalies:
            interpretation += (
                " Member 4 hydromet screening is contextual only: "
                + hydromet_anomalies[0].evidence
            )
        return RiskResponse(
            project_id=request.project_id, structure=request.structure, assessment_status=assessment_status,
            score=round(score, 2), level=level,
            warning_message=message, interpretation=interpretation, contributing_factors=factors,
            recommended_next_action=action,
            instrument_risks=sorted(instrument_risks, key=lambda item: item.score, reverse=True),
            alerts=sorted(alerts, key=lambda item: {"WATCH": 1, "WARNING": 2, "CRITICAL": 3}[item.severity], reverse=True),
            active_alert_count=len(alerts),
            hydromet_assessment=hydromet_assessment,
            model_version=self.baselines.get("model_version", MODEL_VERSION), assessed_at=assessed_at,
            limitations=[
                "Historical workbooks contain no verified incident labels or approved action levels.",
                "Statistical deviation is not proof of structural danger or safety.",
                "Hydrometeorological values are not scored directly; causal or response claims require validated correlation evidence.",
                "Outputs require review by the project's qualified dam-safety engineer.",
            ],
        )
