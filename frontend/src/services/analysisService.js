import { normalizeUnifiedAnalysis } from "../contracts/unifiedAnalysis";
import { analysisScenarios } from "../mocks/analysisScenarios";
import { apiRequest, USE_MOCK_ANALYSIS } from "./api";

export async function getLatestAnalysis(projectId, scenario = "critical") {
  if (USE_MOCK_ANALYSIS) {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return normalizeUnifiedAnalysis(analysisScenarios[scenario] || analysisScenarios.critical);
  }
  const payload = await apiRequest(`/api/analysis/latest?project_id=${encodeURIComponent(projectId)}`);
  return normalizeUnifiedAnalysis(payload);
}
