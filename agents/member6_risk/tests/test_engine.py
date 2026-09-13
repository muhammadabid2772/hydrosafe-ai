from datetime import datetime, timedelta, timezone

from backend.agents.member6_risk.engine import RiskEngine
from backend.agents.member6_risk.models import HydrometContext, QualityInput, Reading, RiskRequest, SignalInput, ThresholdInput


def request(**changes):
    payload = {"project_id": "test", "structure": "ACCRD", "quality": QualityInput(score=100)}
    payload.update(changes)
    return RiskRequest(**payload)


def test_clean_evidence_is_normal():
    result = RiskEngine().assess(request())
    assert result.level == "NORMAL"
    assert result.score == 0
    assert result.assessment_status == "NOT_ASSESSED"
    assert "not been assessed" in result.warning_message
    assert result.requires_engineer_review is True


def test_stronger_anomaly_never_reduces_risk():
    low = RiskEngine().assess(request(anomalies=[SignalInput(score=20, evidence="low")]))
    high = RiskEngine().assess(request(anomalies=[SignalInput(score=90, evidence="high")]))
    assert high.score > low.score
    assert high.assessment_status == "ASSESSED"


def test_missing_quality_is_visible_uncertainty():
    result = RiskEngine().assess(RiskRequest(project_id="test", structure="POWER_HOUSE"))
    factor = next(item for item in result.contributing_factors if item.key == "data_quality")
    assert factor.score == 25
    assert "missing" in factor.evidence.lower()


def test_engineer_critical_threshold_drives_critical_output():
    result = RiskEngine().assess(request(
        readings=[Reading(instrument_id="P01DS3", metric="pressure", value=12)],
        thresholds=[ThresholdInput(instrument_id="P01DS3", metric="pressure", critical_above=10, source="approved plan")],
    ))
    assert result.level == "CRITICAL"
    assert result.score >= 70
    assert result.active_alert_count == 1
    assert result.alerts[0].severity == "CRITICAL"
    assert result.alerts[0].threshold_value == 10


def test_reading_change_and_daily_rate_are_returned():
    result = RiskEngine().assess(request(readings=[Reading(
        instrument_id="P01DS3", metric="pressure", value=12, previous_value=10,
        previous_timestamp="2025-01-01T00:00:00Z", timestamp="2025-01-03T00:00:00Z",
    )]))
    instrument = result.instrument_risks[0]
    assert instrument.absolute_change == 2
    assert instrument.change_percent == 20
    assert instrument.rate_per_day == 1


def test_hydromet_is_context_not_a_direct_alarm():
    result = RiskEngine().assess(request(hydromet=HydrometContext(
        observed_at=datetime.now(timezone.utc), reservoir_level_m=461.2,
        daily_rainfall_mm=139, rainfall_7d_mm=220, inflow_m3_s=2730,
        source="reviewed hydromet workbook",
    )))
    assert result.level == "NORMAL"
    assert result.score == 0
    assert result.hydromet_assessment.status == "FRESH"
    assert result.hydromet_assessment.direct_risk_contribution == 0


def test_same_day_future_hydromet_time_has_nonnegative_freshness():
    result = RiskEngine().assess(request(hydromet=HydrometContext(
        observed_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        daily_rainfall_mm=10,
        source="test fixture",
    )))
    assert result.hydromet_assessment.status == "FRESH"
    assert result.hydromet_assessment.freshness_days == 0


def test_member4_hydromet_anomaly_is_context_not_structural_score():
    result = RiskEngine().assess(request(anomalies=[SignalInput(
        metric="hydromet_multivariate",
        score=100,
        confidence=1,
        evidence="Member 4 high statistical screen",
        scope="HYDROMET",
        source_agent="member4_anomaly",
        details={"anomaly": True, "severity": "High", "max_abs_z": 5.2},
    )]))
    assert result.level == "NORMAL"
    assert result.score == 0
    assert result.assessment_status == "NOT_ASSESSED"
    assert result.hydromet_assessment.anomaly_detected is True
    assert result.hydromet_assessment.anomaly_severity == "High"
    anomaly_factor = next(item for item in result.contributing_factors if item.key == "anomaly")
    assert anomaly_factor.score == 0


def test_structural_anomaly_remains_backward_compatible():
    implicit = RiskEngine().assess(request(anomalies=[SignalInput(score=80, evidence="structural")]))
    explicit = RiskEngine().assess(request(anomalies=[SignalInput(
        score=80, evidence="structural", scope="STRUCTURAL"
    )]))
    assert implicit.score == explicit.score
    assert implicit.level == explicit.level
