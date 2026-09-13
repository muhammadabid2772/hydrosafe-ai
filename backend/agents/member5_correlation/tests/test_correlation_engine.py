from datetime import datetime, timezone

from backend.agents.member5_correlation import CorrelationEngine
from backend.agents.member6_risk.models import SignalInput


def test_pairwise_positive_correlation_emits_risk_signal():
    rows = []
    for day, value in enumerate([1, 2, 3, 4, 5], start=1):
        stamp = datetime(2026, 1, day, tzinfo=timezone.utc)
        rows.append({"instrument_id": "P1", "metric": "pressure", "value": value, "timestamp": stamp})
        rows.append({"instrument_id": "S1", "metric": "seepage", "value": value * 2, "timestamp": stamp})
    result, signals = CorrelationEngine().analyze(rows, [], [])
    assert result.detected_count == 1
    assert result.evidence[0].coefficient == 1
    assert signals[0].source_agent == "member5_correlation"
    assert signals[0].scope == "STRUCTURAL"


def test_cross_signal_requires_hydromet_and_structural_evidence():
    hydro = SignalInput(score=90, confidence=.9, evidence="hydro", scope="HYDROMET", source_agent="member4_anomaly")
    structural = SignalInput(instrument_id="P1", metric="pressure", score=80, confidence=.9, evidence="trend", scope="STRUCTURAL", source_agent="member3_trends")
    result, signals = CorrelationEngine().analyze([], [structural], [hydro])
    assert result.detected_count == 1
    assert result.evidence[0].evidence_type == "CROSS_SIGNAL_TEMPORAL"
    assert signals[0].score >= 50
