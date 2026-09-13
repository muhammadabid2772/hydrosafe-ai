import { apiRequest, USE_MOCK_API } from "./api";

const DEMO_USER_KEY = "hydrosafe_demo_user";

export async function updateProfile(details) {
  if (!USE_MOCK_API) {
    return apiRequest("/api/settings/profile", { method: "PUT", body: JSON.stringify(details) });
  }
  const current = JSON.parse(sessionStorage.getItem(DEMO_USER_KEY) || "null");
  const user = { ...(current || {}), name: details.name };
  sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(user));
  return { user };
}

export async function changePassword(details) {
  if (!USE_MOCK_API) {
    return apiRequest("/api/settings/password", { method: "PUT", body: JSON.stringify(details) });
  }
  if (details.new_password.length < 8) throw new Error("Use at least eight characters for the new password.");
  return { status: "ok", message: "Password changed for this demo session." };
}
