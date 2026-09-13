import { apiRequest, USE_MOCK_API } from "./api";

const MOCK_REPORTS_KEY = "hydrosafe_demo_reports";

function fallbackContent(analysis) {
  const risk = analysis.risk;
  return `HYDROSAFE AI ENGINEERING MONITORING REPORT\n\nProject: ${analysis.project_id}\nStructure: ${analysis.structure}\nRisk assessment: ${risk.level} (${risk.score}/100)\n\n${risk.interpretation}\n\nRecommended next action\n${risk.recommended_next_action}\n\nEngineering boundary\nThis report supports engineering review and does not replace approved site action levels or emergency procedures.`;
}

export async function generateReport(analysis) {
  if (!USE_MOCK_API) {
    return apiRequest("/api/reports/generate", { method: "POST", body: JSON.stringify({ analysis }) });
  }
  const report = {
    report_id: `demo-${Date.now()}`,
    project_id: analysis.project_id,
    structure: analysis.structure,
    analysis_id: analysis.analysis_id,
    risk_level: analysis.risk.level,
    risk_score: analysis.risk.score,
    title: `${analysis.project_id} — ${analysis.structure} Monitoring Report`,
    content: fallbackContent(analysis),
    ai_enhanced: false,
    provider_status: "DEMO_FALLBACK",
    created_at: new Date().toISOString(),
  };
  const previous = JSON.parse(sessionStorage.getItem(MOCK_REPORTS_KEY) || "[]");
  sessionStorage.setItem(MOCK_REPORTS_KEY, JSON.stringify([report, ...previous].slice(0, 25)));
  return report;
}

export async function listReports() {
  if (!USE_MOCK_API) return apiRequest("/api/reports");
  return JSON.parse(sessionStorage.getItem(MOCK_REPORTS_KEY) || "[]");
}
