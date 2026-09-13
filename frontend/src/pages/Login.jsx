import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import AuthVisual from "../components/layout/AuthVisual";
import FormField from "../components/ui/FormField";
import PageMeta from "../components/ui/PageMeta";
import PasswordField from "../components/ui/PasswordField";
import { useAuth } from "../contexts/AuthContext";
import { USE_MOCK_API } from "../services/api";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState(USE_MOCK_API ? { email: "operator@hydrosafe.demo", password: "DemoSafe1" } : { email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (!/^\S+@\S+\.\S+$/.test(form.email) || form.password.length < 8) {
      setError("Enter a valid email and a password of at least eight characters.");
      return;
    }
    setSubmitting(true);
    try {
      await login(form);
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <PageMeta title="Operator Login | HydroSafe AI" description="Securely access the HydroSafe AI dam safety command center." path="/login" />
      <AuthVisual mode="login" />
      <section className="auth-card">
        <div className="auth-toolbar"><Link to="/" aria-label="Back to HydroSafe home">←</Link><button type="button" aria-label="Authentication help" title="Contact the team lead for account access">?</button></div>
        <div><span className="eyebrow">Authorized access</span><h1>Welcome back.</h1><p>Continue to the active monitoring workspace.</p></div>
        {USE_MOCK_API && <div className="demo-notice">Demo mode is active. The prefilled credentials will work.</div>}
        <form onSubmit={handleSubmit} noValidate>
          <FormField label="Email address" id="login-email" type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          <PasswordField label="Password" id="login-password" autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary button-full" disabled={submitting}>{submitting ? "Logging in…" : "Log in securely"}</button>
        </form>
        <p className="auth-switch">New to HydroSafe? <Link to="/signup">Create an account</Link></p>
      </section>
    </main>
  );
}
