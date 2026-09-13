export default function AuthVisual({ mode }) {
  return (
    <aside className="auth-visual">
      <img src="/auth-operator.webp" alt="Dam safety engineer standing in a monitoring control room" width="788" height="1400" />
      <div className="auth-visual-overlay">
        <span>OPERATOR INTERFACE / 01</span>
        <div><strong>Evidence before escalation.</strong><p>One synchronized view across hydrological load, structural response and verified warnings.</p></div>
        <small>{mode === "signup" ? "Create a project-ready operator profile" : "Continue to the active safety command center"}</small>
      </div>
    </aside>
  );
}
