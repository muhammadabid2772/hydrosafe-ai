from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

from backend.agents.member1_orchestration.models import UnifiedAnalysisResponse


@dataclass
class GeneratedReport:
    title: str
    content: str
    ai_enhanced: bool
    provider_status: str


def deterministic_report(analysis: UnifiedAnalysisResponse) -> str:
    risk = analysis.risk
    factors = "\n".join(
        f"- {item.label}: {item.score:.1f}/100 — {item.evidence}" for item in risk.contributing_factors
    ) or "- No contributing factors were supplied."
    correlations = "\n".join(
        f"- {item.get('explanation', item.get('evidence', 'Correlation evidence supplied.'))}"
        for item in analysis.correlations if item.get("correlation_detected", True)
    ) or "- No material correlation was detected from the supplied evidence."
    anomalies = "\n".join(
        f"- {item.get('evidence', 'Anomaly evidence supplied.')}" for item in analysis.anomalies if float(item.get("score", 0) or 0) >= 50
    ) or "- No material structural anomaly signal was emitted."
    return f"""HYDROSAFE AI ENGINEERING MONITORING REPORT

Project: {analysis.project_id}
Structure: {analysis.structure}
Analysis ID: {analysis.analysis_id}
Data mode: {analysis.data_mode}
Source: {analysis.source}

1. Executive monitoring summary
Risk assessment: {risk.level} ({risk.score:.1f}/100)
Assessment status: {risk.assessment_status}
{risk.warning_message}

2. Evidence interpretation
{risk.interpretation}

3. Data quality and trend coverage
Validation score: {analysis.quality.get('score') if analysis.quality.get('score') is not None else 'Unavailable'}
Trend status: {analysis.trends.get('status', 'UNAVAILABLE')}

4. Contributing factors
{factors}

5. Anomaly evidence
{anomalies}

6. Correlation evidence
{correlations}

7. Recommended next action
{risk.recommended_next_action}

8. Engineering limitations
- This report is decision-support evidence, not a declaration of dam safety or failure probability.
- Statistical anomalies and correlations require validation against approved site action levels and engineering judgement.
- Historical replay data must not be presented as live telemetry.
- Qualified dam-safety review remains mandatory before operational action.
""".strip()


def _openrouter_text(analysis: UnifiedAnalysisResponse, base_report: str) -> str | None:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    prompt = {
        "analysis": analysis.model_dump(mode="json"),
        "draft": base_report,
    }
    instructions = (
        "Rewrite the supplied HydroSafe engineering monitoring draft into a concise professional report. "
        "Use only facts present in the supplied JSON and draft. Do not invent thresholds, causes, failure probabilities, live status, or measurements. "
        "Keep the numbered sections, preserve all safety limitations, clearly distinguish correlation from causation, and return plain text only."
    )
    try:
        with httpx.Client(timeout=25) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.1,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": json.dumps(prompt, default=str)},
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return content or None
    except Exception:
        return None


def generate_report(analysis: UnifiedAnalysisResponse) -> GeneratedReport:
    base = deterministic_report(analysis)
    enhanced = _openrouter_text(analysis, base)
    content = enhanced or base
    return GeneratedReport(
        title=f"{analysis.project_id} — {analysis.structure} Monitoring Report",
        content=content,
        ai_enhanced=enhanced is not None,
        provider_status="AI_ENHANCED" if enhanced is not None else "DETERMINISTIC_FALLBACK",
    )
