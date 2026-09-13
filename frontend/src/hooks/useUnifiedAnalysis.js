import { useCallback, useEffect, useState } from "react";
import { getLatestAnalysis } from "../services/analysisService";

export function useUnifiedAnalysis(projectId, scenario) {
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setAnalysis(await getLatestAnalysis(projectId, scenario));
    } catch (requestError) {
      setError(requestError.message || "Analysis could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [projectId, scenario]);

  useEffect(() => { refresh(); }, [refresh]);
  return { analysis, error, loading, refresh };
}
