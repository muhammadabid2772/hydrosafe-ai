from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from itertools import combinations
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from backend.agents.member6_risk.models import SignalInput


MODEL_VERSION = "member5-correlation-v1"
MIN_PAIRED_POINTS = 4
DETECTION_THRESHOLD = 0.70


class CorrelationEvidence(BaseModel):
    evidence_type: str
    correlation_detected: bool
    confidence: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=100)
    related_parameters: list[str]
    explanation: str
    coefficient: float | None = None
    paired_points: int | None = None
    observed_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CorrelationResult(BaseModel):
    available: bool
    status: str
    agent: str = "member5_correlation"
    model_version: str = MODEL_VERSION
    evidence_count: int
    detected_count: int
    evidence: list[CorrelationEvidence]
    limitations: list[str]


class CorrelationEngine:
    """Evidence-based correlation engine for hackathon MVP use.

    It combines exact-timestamp Pearson co-movement where paired series exist with
    deterministic cross-signal reasoning between Member 4 hydromet context and
    structural trend/anomaly signals. It never labels correlation as causation.
    """

    def _pairwise(self, rows: list[dict[str, Any]]) -> list[CorrelationEvidence]:
        grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
        observed: dict[tuple[str, str], datetime] = {}
        for row in rows:
            key = (str(row["instrument_id"]), str(row["metric"]))
            timestamp = row["timestamp"] if isinstance(row["timestamp"], datetime) else datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
            grouped[key][timestamp.isoformat()] = float(row["value"])
            observed[key] = max(timestamp, observed.get(key, timestamp))

        output: list[CorrelationEvidence] = []
        for left, right in combinations(sorted(grouped), 2):
            common = sorted(set(grouped[left]).intersection(grouped[right]))
            if len(common) < MIN_PAIRED_POINTS:
                continue
            left_values = np.asarray([grouped[left][stamp] for stamp in common], dtype=float)
            right_values = np.asarray([grouped[right][stamp] for stamp in common], dtype=float)
            if float(np.std(left_values)) <= 1e-12 or float(np.std(right_values)) <= 1e-12:
                continue
            coefficient = float(np.corrcoef(left_values, right_values)[0, 1])
            if not np.isfinite(coefficient):
                continue
            strength = abs(coefficient)
            detected = strength >= DETECTION_THRESHOLD
            score = round(strength * 100, 2)
            confidence = min(0.97, 0.45 + min(len(common), 24) / 24 * 0.5)
            left_name = f"{left[0]}:{left[1]}"
            right_name = f"{right[0]}:{right[1]}"
            direction = "positive" if coefficient >= 0 else "inverse"
            explanation = (
                f"{left_name} and {right_name} show {direction} co-movement (r={coefficient:.2f}) across "
                f"{len(common)} matched timestamps. This is association evidence, not proof of causation."
            )
            output.append(CorrelationEvidence(
                evidence_type="PEARSON_TEMPORAL",
                correlation_detected=detected,
                confidence=round(confidence, 3),
                score=score,
                related_parameters=[left_name, right_name],
                explanation=explanation,
                coefficient=round(coefficient, 4),
                paired_points=len(common),
                observed_at=max(observed[left], observed[right]),
            ))
        return output

    def _cross_signal(self, trends: list[SignalInput], anomalies: list[SignalInput]) -> list[CorrelationEvidence]:
        hydromet = [item for item in anomalies if item.scope == "HYDROMET" and item.score >= 50]
        structural = [item for item in [*trends, *anomalies] if item.scope == "STRUCTURAL" and item.score >= 50]
        output: list[CorrelationEvidence] = []
        if not hydromet or not structural:
            return output

        strongest_hydro = max(hydromet, key=lambda item: item.score * item.confidence)
        for signal in sorted(structural, key=lambda item: item.score * item.confidence, reverse=True)[:4]:
            score = min(100.0, 0.45 * strongest_hydro.score + 0.55 * signal.score)
            confidence = min(0.88, strongest_hydro.confidence * signal.confidence)
            parameter = ":".join(part for part in [signal.instrument_id, signal.metric] if part) or "structural signal"
            explanation = (
                f"Hydrometeorological anomaly context overlaps in time with elevated structural evidence for {parameter}. "
                "The signals are treated as a correlated monitoring pattern only; engineering review is required before any causal interpretation."
            )
            output.append(CorrelationEvidence(
                evidence_type="CROSS_SIGNAL_TEMPORAL",
                correlation_detected=True,
                confidence=round(confidence, 3),
                score=round(score, 2),
                related_parameters=["hydromet_context", parameter],
                explanation=explanation,
                observed_at=signal.observed_at or strongest_hydro.observed_at,
                details={
                    "hydromet_source": strongest_hydro.source_agent,
                    "structural_source": signal.source_agent,
                    "hydromet_score": strongest_hydro.score,
                    "structural_score": signal.score,
                },
            ))
        return output

    def analyze(
        self,
        rows: list[dict[str, Any]],
        trends: list[SignalInput],
        anomalies: list[SignalInput],
    ) -> tuple[CorrelationResult, list[SignalInput]]:
        evidence = [*self._pairwise(rows), *self._cross_signal(trends, anomalies)]
        detected = [item for item in evidence if item.correlation_detected]
        signals = [
            SignalInput(
                metric="correlation",
                score=item.score,
                confidence=item.confidence,
                evidence=item.explanation,
                scope="STRUCTURAL",
                source_agent="member5_correlation",
                observed_at=item.observed_at,
                details={
                    "evidence_type": item.evidence_type,
                    "related_parameters": item.related_parameters,
                    "coefficient": item.coefficient,
                    "paired_points": item.paired_points,
                },
            )
            for item in detected
        ]
        result = CorrelationResult(
            available=bool(evidence),
            status="DETECTED" if detected else "NO_DETECTION" if evidence else "INSUFFICIENT_DATA",
            evidence_count=len(evidence),
            detected_count=len(detected),
            evidence=evidence,
            limitations=[
                "Correlation is association evidence and must not be presented as causation.",
                f"Pearson evidence requires at least {MIN_PAIRED_POINTS} exact timestamp pairs and |r| >= {DETECTION_THRESHOLD:.2f} for detection.",
                "Hydromet-to-structural cross-signal evidence requires both an elevated hydromet anomaly and elevated structural trend/anomaly evidence.",
                "No labelled hydro-structural failure dataset is bundled, so this MVP uses deterministic evidence rules rather than a trained classifier.",
            ],
        )
        return result, signals
