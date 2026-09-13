import test from "node:test";
import assert from "node:assert/strict";
import { normalizeUnifiedAnalysis } from "../src/contracts/unifiedAnalysis.js";
import { analysisScenarios } from "../src/mocks/analysisScenarios.js";
import { buildAnomalyRequest, validateConditions } from "../src/features/member4-anomaly/anomalyForm.js";
import { formatUnit, formatUtcTimestamp } from "../src/utils/format.js";

test("normalizes all four deterministic risk states", () => {
  for (const [name, payload] of Object.entries(analysisScenarios)) {
    const result = normalizeUnifiedAnalysis(payload);
    assert.equal(result.risk.level, name.toUpperCase());
    assert.ok(result.risk.score >= 0 && result.risk.score <= 100);
    assert.ok(result.risk.warning_message.length > 0);
    assert.ok(result.risk.recommended_next_action.length > 0);
  }
});

test("does not invent a risk level when upstream risk is missing", () => {
  const result = normalizeUnifiedAnalysis({});
  assert.equal(result.risk.level, "UNKNOWN");
  assert.equal(result.risk.score, null);
  assert.equal(result.risk.assessment_status, "NOT_ASSESSED");
});

test("clamps malformed scores for safe presentation", () => {
  assert.equal(normalizeUnifiedAnalysis({ risk: { score: 140, level: "CRITICAL" } }).risk.score, 100);
  assert.equal(normalizeUnifiedAnalysis({ risk: { score: -4, level: "NORMAL" } }).risk.score, 0);
});

test("keeps Member 4 hydromet evidence contextual", () => {
  const result = normalizeUnifiedAnalysis(analysisScenarios.critical);
  assert.equal(result.risk.hydromet_assessment.anomaly_source, "member4_anomaly");
  assert.equal(result.risk.hydromet_assessment.direct_risk_contribution, 0);
  assert.equal(result.risk.hydromet_assessment.anomaly_detected, true);
});

test("builds the integrated Member 4 and Risk Agent request", () => {
  const values = { reservoir_level: "459.04", tailwater: "391.69", inflow: "490", rainfall: "49", temperature: "24.8" };
  const payload = buildAnomalyRequest({ values, observedAt: "2026-09-13T08:00", structure: "ACCRD" });
  assert.equal(payload.risk.structure, "ACCRD");
  assert.equal("quality" in payload.risk, false);
  assert.equal(payload.current_hydromet.rainfall, 49);
  assert.match(payload.observed_at, /^2026-09-13T/);
});

test("keeps critical Member 4 mock severity and evidence consistent", () => {
  const assessment = analysisScenarios.critical.risk.hydromet_assessment;
  assert.equal(assessment.anomaly_severity, "High");
  assert.match(assessment.anomaly_evidence[0], /high hydrometeorological screen/i);
});

test("formats operational timestamps and units unambiguously", () => {
  assert.equal(formatUtcTimestamp("2026-09-13T13:04:00Z"), "2026-09-13 13:04 UTC");
  assert.equal(formatUnit("m3/s"), "m³/s");
  assert.equal(formatUnit("C"), "°C");
});

test("rejects invalid hydrometeorological entries before API submission", () => {
  const errors = validateConditions({ reservoir_level: "", tailwater: "391", inflow: "-2", rainfall: "-1", temperature: "25" });
  assert.ok(errors.reservoir_level);
  assert.ok(errors.inflow);
  assert.ok(errors.rainfall);
});

test("keeps valid zero trend and quality scores distinct from unavailable results", () => {
  const result = normalizeUnifiedAnalysis({
    quality: { available: true, score: 0, total_records: 2, valid_count: 0, flagged_count: 2 },
    trends: { available: true, status: "READY", series: [{ instrument_id: "P1", metric: "pressure", available: true, score: 0, chart_points: [] }] },
    risk: { assessment_status: "NOT_ASSESSED", score: 0, level: "NORMAL" },
  });
  assert.equal(result.quality.available, true);
  assert.equal(result.quality.score, 0);
  assert.equal(result.trends.available, true);
  assert.equal(result.trends.series[0].score, 0);
});

test("represents absent quality and trends as unavailable", () => {
  const result = normalizeUnifiedAnalysis({ risk: {} });
  assert.equal(result.quality.available, false);
  assert.equal(result.quality.score, null);
  assert.equal(result.trends.available, false);
  assert.deepEqual(result.trends.series, []);
});
