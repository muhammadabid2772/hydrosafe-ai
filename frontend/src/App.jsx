import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import ProtectedRoute from "./components/layout/ProtectedRoute";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Monitoring = lazy(() => import("./pages/Monitoring"));
const AnomalyDetector = lazy(() => import("./pages/AnomalyDetector"));
const Correlations = lazy(() => import("./pages/Correlations"));
const Reports = lazy(() => import("./pages/Reports"));
const Settings = lazy(() => import("./pages/Settings"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const NotFound = lazy(() => import("./pages/NotFound"));

export default function App() {
  const location = useLocation();
  const isDashboard = location.pathname.startsWith("/dashboard");

  return (
    <div className="app-shell">
      {!isDashboard && <Navbar />}
      <Suspense fallback={<main className="route-loader" aria-live="polite"><span />Loading HydroSafe…</main>}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/monitoring" element={<Monitoring />} />
            <Route path="/dashboard/anomalies" element={<AnomalyDetector />} />
            <Route path="/dashboard/correlations" element={<Correlations />} />
            <Route path="/dashboard/reports" element={<Reports />} />
            <Route path="/dashboard/settings" element={<Settings />} />
          </Route>
          <Route path="/home" element={<Navigate to="/" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </div>
  );
}
