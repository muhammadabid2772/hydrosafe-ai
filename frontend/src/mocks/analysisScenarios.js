const base = {
  analysis_id: "analysis-demo-2026-09-12",
  project_id: "demo-dam-01",
  generated_at: "2026-09-12T10:30:00Z",
  quality: { score: 96, valid_records: 116, flagged_records: 4, sensor_health: "GOOD" },
  trends: {
    reservoir_level: { direction: "INCREASING", percent_change: 6.3 },
    seepage: { direction: "INCREASING", percent_change: 14.8 },
    piezometer: { direction: "INCREASING", percent_change: 9.2 },
  },
  anomalies: [],
  correlations: [],
  report: { status: "READY", report_id: "report-demo-01" },
};

const hydrometAssessment = {
  supplied: true,
  status: "FRESH",
  observed_at: "2026-09-12T10:30:00Z",
  freshness_days: 0,
  summary: "Hydromet context is fresh: reservoir 459.8 m, daily rainfall 49 mm, inflow 490 m³/s.",
  direct_risk_contribution: 0,
  anomaly_signal_count: 1,
  anomaly_detected: true,
  anomaly_severity: "Moderate",
  anomaly_source: "member4_anomaly",
  anomaly_evidence: ["Moderate hydrometeorological screen; Rainfall |z|=2.73. Context only; structural corroboration is required."],
};

export const analysisScenarios = {
  normal: {
    ...base,
    risk: {
      assessment_status: "ASSESSED",
      score: 18,
      level: "NORMAL",
      hydromet_assessment: { ...hydrometAssessment, anomaly_detected: false, anomaly_severity: "Normal", anomaly_evidence: [] },
      warning_message: "All monitored indicators remain within expected operating ranges.",
      contributing_factors: [
        { key: "data_quality", label: "Data quality", score: 4, weight: 0.1, evidence: "96% quality score" },
        { key: "hydrology", label: "Hydrological load", score: 17, weight: 0.3, evidence: "Reservoir change remains controlled" },
        { key: "structural", label: "Structural response", score: 20, weight: 0.35, evidence: "No abnormal seepage response" },
      ],
      recommended_next_action: "Continue routine monitoring at the current sampling interval.",
    },
  },
  watch: {
    ...base,
    risk: {
      assessment_status: "ASSESSED",
      score: 42,
      level: "WATCH",
      hydromet_assessment: hydrometAssessment,
      warning_message: "Reservoir and inflow are rising. Increased observation is advised.",
      contributing_factors: [
        { key: "hydrology", label: "Hydrological load", score: 58, weight: 0.3, evidence: "Reservoir level increased 6.3%" },
        { key: "trend", label: "Trend acceleration", score: 44, weight: 0.2, evidence: "Inflow trend is increasing" },
        { key: "structural", label: "Structural response", score: 27, weight: 0.35, evidence: "Pressure remains below warning threshold" },
      ],
      recommended_next_action: "Increase review frequency and verify upstream rainfall observations.",
    },
  },
  warning: {
    ...base,
    anomalies: [{ sensor: "seepage", severity: "HIGH", confidence: 0.82 }],
    risk: {
      assessment_status: "ASSESSED",
      score: 63,
      level: "WARNING",
      hydromet_assessment: hydrometAssessment,
      warning_message: "Seepage and piezometric pressure are increasing alongside reservoir load.",
      contributing_factors: [
        { key: "anomaly", label: "Anomaly severity", score: 78, weight: 0.25, evidence: "High seepage anomaly detected" },
        { key: "structural", label: "Structural response", score: 69, weight: 0.35, evidence: "Seepage increased 14.8%" },
        { key: "hydrology", label: "Hydrological load", score: 61, weight: 0.3, evidence: "Reservoir level increased 6.3%" },
      ],
      recommended_next_action: "Notify the duty engineer and validate seepage instrumentation immediately.",
    },
  },
  critical: {
    ...base,
    anomalies: [
      { sensor: "seepage", severity: "CRITICAL", confidence: 0.94 },
      { sensor: "piezometer", severity: "HIGH", confidence: 0.89 },
    ],
    correlations: [{ correlation_detected: true, confidence: 0.91, related_parameters: ["rainfall", "inflow", "reservoir_level", "piezometer", "seepage"] }],
    risk: {
      assessment_status: "ASSESSED",
      score: 84,
      level: "CRITICAL",
      hydromet_assessment: {
        ...hydrometAssessment,
        anomaly_severity: "High",
        anomaly_evidence: ["High hydrometeorological screen; rainfall is the leading deviation. Context only; structural corroboration is required."],
      },
      warning_message: "A correlated hydro-structural anomaly requires immediate engineering response.",
      contributing_factors: [
        { key: "correlation", label: "Correlation strength", score: 91, weight: 0.25, evidence: "Five-parameter response chain detected" },
        { key: "anomaly", label: "Anomaly severity", score: 94, weight: 0.25, evidence: "Critical seepage anomaly" },
        { key: "structural", label: "Structural response", score: 86, weight: 0.35, evidence: "Pressure and seepage rising together" },
      ],
      recommended_next_action: "Escalate to the dam safety lead, confirm sensors, and initiate the emergency inspection checklist.",
    },
  },
};
