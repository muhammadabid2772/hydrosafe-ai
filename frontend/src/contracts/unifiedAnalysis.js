export const RISK_LEVELS = ["NORMAL", "WATCH", "WARNING", "CRITICAL"];

function finiteOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function normalizeQuality(value) {
  if (!value || typeof value !== "object") return { available: false, score: null, sensor_health: {}, flags: [] };
  return {
    ...value,
    available: value.available !== false && finiteOrNull(value.score) !== null,
    score: finiteOrNull(value.score),
    total_records: finiteOrNull(value.total_records),
    valid_count: finiteOrNull(value.valid_count ?? value.valid_records),
    flagged_count: finiteOrNull(value.flagged_count ?? value.flagged_records),
    sensor_health: value.sensor_health && typeof value.sensor_health === "object" ? value.sensor_health : {},
    flags: Array.isArray(value.flags) ? value.flags : [],
  };
}

function normalizeTrends(value) {
  if (!value || typeof value !== "object") return { available: false, status: "UNAVAILABLE", series: [] };
  if (Array.isArray(value.series)) {
    const series = value.series.map((item) => ({ ...item, available: item.available !== false, chart_points: Array.isArray(item.chart_points) ? item.chart_points : [] }));
    return { ...value, available: value.available !== false && series.some((item) => item.available), series };
  }
  const legacySeries = Object.entries(value)
    .filter(([, item]) => item && typeof item === "object" && "direction" in item)
    .map(([metric, item]) => ({
      instrument_id: metric, metric, trend: String(item.direction).toLowerCase(),
      percentage_change: finiteOrNull(item.percent_change), rate_of_change: null,
      rate_unit: null, score: null, confidence: null, available: true,
      status: "DEMO", chart_points: [],
    }));
  return { available: legacySeries.length > 0, status: legacySeries.length ? "DEMO" : "UNAVAILABLE", series: legacySeries };
}

export function normalizeUnifiedAnalysis(payload) {
  if (!payload || typeof payload !== "object") throw new TypeError("Unified analysis payload must be an object.");
  const risk = payload.risk || {};
  const numericScore = Number(risk.score);

  return {
    analysis_id: String(payload.analysis_id || "unknown"),
    project_id: String(payload.project_id || "unknown"),
    generated_at: payload.generated_at || null,
    structure: String(payload.structure || "unknown"),
    data_mode: ["LIVE", "HISTORICAL_REPLAY", "OPERATOR_INPUT"].includes(payload.data_mode) ? payload.data_mode : "UNKNOWN",
    source: String(payload.source || "Source not supplied"),
    source_observed_at: payload.source_observed_at || null,
    quality: normalizeQuality(payload.quality),
    trends: normalizeTrends(payload.trends),
    anomalies: Array.isArray(payload.anomalies) ? payload.anomalies : [],
    correlations: Array.isArray(payload.correlations) ? payload.correlations : [],
    risk: {
      ...risk,
      assessment_status: risk.assessment_status === "ASSESSED" ? "ASSESSED" : "NOT_ASSESSED",
      score: Number.isFinite(numericScore) ? Math.min(100, Math.max(0, numericScore)) : null,
      level: RISK_LEVELS.includes(risk.level) ? risk.level : "UNKNOWN",
      warning_message: String(risk.warning_message || "Risk assessment has not been supplied."),
      interpretation: String(risk.interpretation || risk.warning_message || "Risk interpretation has not been supplied."),
      contributing_factors: Array.isArray(risk.contributing_factors) ? risk.contributing_factors : [],
      alerts: Array.isArray(risk.alerts) ? risk.alerts : [],
      active_alert_count: Number.isInteger(risk.active_alert_count) ? Math.max(0, risk.active_alert_count) : 0,
      hydromet_assessment: risk.hydromet_assessment || {
        supplied: false,
        status: "NOT_SUPPLIED",
        summary: "No hydrometeorological context was supplied.",
        direct_risk_contribution: 0,
        anomaly_signal_count: 0,
        anomaly_detected: false,
        anomaly_evidence: [],
      },
      recommended_next_action: String(risk.recommended_next_action || "Wait for the unified analysis pipeline."),
    },
    report: payload.report || {},
  };
}
