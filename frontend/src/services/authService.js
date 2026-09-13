import { apiRequest, USE_MOCK_API } from "./api";

const DEMO_USER_KEY = "hydrosafe_demo_user";
const TOKEN_KEY = "hydrosafe_demo_token";

const delay = (milliseconds = 350) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function saveDemoSession(user) {
  sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(user));
  sessionStorage.setItem(TOKEN_KEY, "demo-session-not-for-production");
  return { user, access_token: "demo-session-not-for-production", token_type: "bearer" };
}

export async function loginUser(credentials) {
  if (!USE_MOCK_API) {
    const result = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    sessionStorage.setItem(TOKEN_KEY, result.access_token);
    return result;
  }
  await delay();
  return saveDemoSession({ id: "demo-user-6", name: "HydroSafe Operator", email: credentials.email });
}

export async function signupUser(details) {
  if (!USE_MOCK_API) {
    const result = await apiRequest("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify(details),
    });
    sessionStorage.setItem(TOKEN_KEY, result.access_token);
    return result;
  }
  await delay();
  return saveDemoSession({ id: "demo-user-6", name: details.name, email: details.email });
}

export async function getCurrentUser() {
  if (!USE_MOCK_API) return apiRequest("/api/auth/me");
  await delay(100);
  const stored = sessionStorage.getItem(DEMO_USER_KEY);
  return stored ? JSON.parse(stored) : null;
}

export async function logoutUser() {
  if (!USE_MOCK_API) {
    try {
      await apiRequest("/api/auth/logout", { method: "POST" });
    } finally {
      sessionStorage.removeItem(TOKEN_KEY);
    }
  }
  sessionStorage.removeItem(DEMO_USER_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

