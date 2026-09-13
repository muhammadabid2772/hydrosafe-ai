import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, loginUser, logoutUser, signupUser } from "../services/authService";
import { changePassword, updateProfile } from "../services/settingsService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setInitializing(false));
  }, []);

  const value = useMemo(() => ({
    user,
    initializing,
    async login(credentials) {
      const result = await loginUser(credentials);
      setUser(result.user);
      return result;
    },
    async signup(details) {
      const result = await signupUser(details);
      setUser(result.user);
      return result;
    },
    async logout() {
      await logoutUser();
      setUser(null);
    },
    async updateProfile(details) {
      const result = await updateProfile(details);
      setUser(result.user);
      return result;
    },
    async changePassword(details) {
      return changePassword(details);
    },
  }), [user, initializing]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

