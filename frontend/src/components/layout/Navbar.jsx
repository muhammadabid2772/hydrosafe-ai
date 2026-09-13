import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

function DropMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 36 36" aria-hidden="true">
      <path d="M18 3C25 12 30 18 30 24a12 12 0 0 1-24 0c0-6 5-12 12-21Z" />
      <path className="brand-wave" d="M11 24c4 2.5 9.5 2.5 14 0" />
    </svg>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  function sectionLink(section) {
    return location.pathname === "/" ? `#${section}` : `/#${section}`;
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <header className="navbar" id="site-navigation">
      <Link to="/" className="brand" aria-label="HydroSafe AI home">
        <DropMark />
        <span>HydroSafe <b>AI</b></span>
      </Link>
      <nav className={menuOpen ? "is-open" : ""} aria-label="Primary navigation">
        <a onClick={() => setMenuOpen(false)} href={sectionLink("home")}>Home</a>
        <a onClick={() => setMenuOpen(false)} href={sectionLink("about")}>About</a>
        <a onClick={() => setMenuOpen(false)} href={sectionLink("features")}>Features</a>
        <a onClick={() => setMenuOpen(false)} href={sectionLink("workflow")}>How it works</a>
        <a onClick={() => setMenuOpen(false)} href={sectionLink("safety")}>Safety</a>
      </nav>
      <div className="nav-actions">
        {user ? (
          <>
            <span className="user-chip">{user.name || user.email}</span>
            <button className="button button-ghost button-small" onClick={handleLogout}>Log out</button>
          </>
        ) : (
          <>
            <Link className="button button-ghost button-small" to="/login">Log in</Link>
            <Link className="button button-primary button-small" to="/signup">Create account</Link>
          </>
        )}
      </div>
      <button className="mobile-menu-toggle" type="button" aria-label={menuOpen ? "Close navigation" : "Open navigation"} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>
        {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
      </button>
    </header>
  );
}
