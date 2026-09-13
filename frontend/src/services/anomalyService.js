import { apiRequest } from "./api";

function signalFromTrend(item) {
  return {
    instrument_id: item.instrument_id,
    metric: item.metric,
    score: Number(item.score || 0),
    confidence: Number(item.confidence ?? 1),
    evidence: item.evidence || `${item.instrument_id} ${item.metric} trend evidence`,
    scope: "STRUCTURAL",
    source_agent: "member3_trends",
    observed_at: item.chart_points?.at(-1)?.timestamp || null,
    details: { trend: item.trend, rate_of_change: item.rate_of_change, percentage_change: item.percentage_change },
  };
}

function riskFromAnalysis(analysis) {
  return {
    project_id: analysis.project_id,
    structure: analysis.structure,
    readings: (analysis.risk?.instrument_risks || []).map((item) => ({
      instrument_id: item.instrument_id,
      metric: item.metric,
      value: item.current_value,
      previous_value: item.previous_value,
    })),
    quality: analysis.quality?.available ? {
      score: analysis.quality.score,
      missing_rate: analysis.quality.total_records ? analysis.quality.flagged_count / analysis.quality.total_records : null,
      evidence: `Unified structural validation quality ${analysis.quality.score}/100.`,
    } : undefined,
    trends: (analysis.trends?.series || []).filter((item) => item.available).map(signalFromTrend),
    anomalies: (analysis.anomalies || []).filter((item) => item.scope !== "HYDROMET"),
    correlations: (analysis.correlations || []).filter((item) => item.correlation_detected).map((item) => ({
      metric: "correlation",
      score: Number(item.score || 0),
      confidence: Number(item.confidence ?? 1),
      evidence: item.explanation || "Correlation evidence supplied by Agent 5.",
      scope: "STRUCTURAL",
      source_agent: "member5_correlation",
      observed_at: item.observed_at || null,
      details: { related_parameters: item.related_parameters, coefficient: item.coefficient, evidence_type: item.evidence_type },
    })),
    context: { source_analysis_id: analysis.analysis_id, evidence_mode: "LATEST_VALIDATED_STRUCTURAL" },
  };
}

export async function assessMember4Anomaly(payload) {
  let enriched = payload;
  if (payload.risk?.structure === "ACCRD" && !(payload.risk?.readings || []).length) {
    try {
      const analysis = await apiRequest(`/api/analysis/latest?project_id=${encodeURIComponent(payload.risk.project_id || "demo-dam-01")}`);
      enriched = { ...payload, risk: riskFromAnalysis(analysis) };
    } catch {
      // Keep the standalone hydromet screen available even if structural evidence cannot be loaded.
    }
  }
  return apiRequest("/api/risk/assess-with-member4", {
    method: "POST",
    body: JSON.stringify(enriched),
  });
}
