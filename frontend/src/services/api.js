const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === "true";
export const USE_MOCK_ANALYSIS = import.meta.env.VITE_USE_MOCK_ANALYSIS === "true";

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function apiRequest(path, options = {}) {
  const token = sessionStorage.getItem("hydrosafe_demo_token");
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("The HydroSafe service is unavailable. Check the backend connection and try again.");
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const safeMessage = response.status === 401
      ? "The email or password is incorrect."
      : payload?.message || payload?.detail || "The request could not be completed.";
    throw new ApiError(safeMessage, response.status, payload);
  }

  return payload;
}
