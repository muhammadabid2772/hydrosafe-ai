import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import AuthVisual from "../components/layout/AuthVisual";
import FormField from "../components/ui/FormField";
import PageMeta from "../components/ui/PageMeta";
import PasswordField from "../components/ui/PasswordField";
import { useAuth } from "../contexts/AuthContext";
import { USE_MOCK_API } from "../services/api";

export default function Signup() {
  const { user, signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (form.name.trim().length < 2 || !/^\S+@\S+\.\S+$/.test(form.email)) return setError("Enter your name and a valid email address.");
    if (form.password.length < 8) return setError("Use at least eight characters for the password.");
    if (form.password !== form.confirmPassword) return setError("The passwords do not match.");
    setSubmitting(true);
    try {
      await signup({ name: form.name.trim(), email: form.email, password: form.password });
      navigate("/dashboard", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <PageMeta title="Create Operator Account | HydroSafe AI" description="Create a HydroSafe AI operator account for project-based dam monitoring." path="/signup" />
      <AuthVisual mode="signup" />
      <section className="auth-card">
        <div className="auth-toolbar"><Link to="/" aria-label="Back to HydroSafe home">←</Link><button type="button" aria-label="Authentication help" title="Contact the team lead for account access">?</button></div>
        <div><span className="eyebrow">New operator</span><h1>Create account.</h1><p>Set up access for project monitoring and warning history.</p></div>
        {USE_MOCK_API && <div className="demo-notice">Demo mode stores only a temporary session in this browser tab.</div>}
        <form onSubmit={handleSubmit} noValidate>
          <FormField label="Full name" id="signup-name" type="text" autoComplete="name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          <FormField label="Email address" id="signup-email" type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          <PasswordField label="Password" id="signup-password" autoComplete="new-password" hint="Use at least eight characters." value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
          <PasswordField label="Confirm password" id="signup-confirm" autoComplete="new-password" value={form.confirmPassword} onChange={(event) => setForm({ ...form, confirmPassword: event.target.value })} required />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary button-full" disabled={submitting}>{submitting ? "Creating account…" : "Create operator account"}</button>
        </form>
        <p className="auth-switch">Already registered? <Link to="/login">Log in</Link></p>
      </section>
    </main>
  );
}
