import { useEffect, useState } from "react";
import DashboardSidebar from "../components/layout/DashboardSidebar";
import PasswordField from "../components/ui/PasswordField";
import FormField from "../components/ui/FormField";
import PageMeta from "../components/ui/PageMeta";
import { useAuth } from "../contexts/AuthContext";

export default function Settings() {
  const { user, updateProfile, changePassword } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "", confirm: "" });
  const [profileStatus, setProfileStatus] = useState("");
  const [passwordStatus, setPasswordStatus] = useState("");

  useEffect(() => setName(user?.name || ""), [user]);

  async function saveProfile(event) {
    event.preventDefault(); setProfileStatus("");
    try { await updateProfile({ name }); setProfileStatus("Profile updated."); }
    catch (error) { setProfileStatus(error.message || "Profile update failed."); }
  }

  async function savePassword(event) {
    event.preventDefault(); setPasswordStatus("");
    if (passwords.new_password !== passwords.confirm) return setPasswordStatus("New passwords do not match.");
    try {
      const result = await changePassword({ current_password: passwords.current_password, new_password: passwords.new_password });
      setPasswordStatus(result.message || "Password changed successfully.");
      setPasswords({ current_password: "", new_password: "", confirm: "" });
    } catch (error) { setPasswordStatus(error.message || "Password update failed."); }
  }

  return (
    <div className="dashboard-shell">
      <PageMeta title="Account Settings | HydroSafe AI" description="Manage your HydroSafe operator profile and password." path="/dashboard/settings" />
      <DashboardSidebar />
      <main className="dashboard-page settings-page">
        <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="/">HydroSafe</a><span>/</span><span>Account</span><span>/</span><strong>Settings</strong></nav>
        <header className="dashboard-header"><div><span className="eyebrow">Operator account</span><h1>Settings</h1><p>Manage your profile and security credentials.</p></div></header>
        <div className="settings-grid">
          <form className="panel settings-card" onSubmit={saveProfile}><span className="eyebrow">Profile</span><h2>Operator details</h2><FormField label="Display name" id="settings-name" value={name} onChange={(event) => setName(event.target.value)} required /><FormField label="Email address" id="settings-email" value={user?.email || ""} disabled /><button className="button button-primary">Save profile</button>{profileStatus && <p className="settings-status">{profileStatus}</p>}</form>
          <form className="panel settings-card" onSubmit={savePassword}><span className="eyebrow">Security</span><h2>Change password</h2><PasswordField label="Current password" id="current-password" value={passwords.current_password} onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })} required /><PasswordField label="New password" id="new-password" value={passwords.new_password} onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })} required /><PasswordField label="Confirm new password" id="confirm-new-password" value={passwords.confirm} onChange={(event) => setPasswords({ ...passwords, confirm: event.target.value })} required /><button className="button button-primary">Change password</button>{passwordStatus && <p className="settings-status">{passwordStatus}</p>}</form>
        </div>
      </main>
    </div>
  );
}
