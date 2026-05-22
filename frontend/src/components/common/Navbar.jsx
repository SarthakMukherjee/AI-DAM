import { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthContext from "../../context/AuthContext";
import NotificationBell from "./NotificationBell";
import "../../styles/navbar.css";

const ROLE_LABEL = {
  user: "User",
  admin: "Admin",
  reviewer: "Reviewer",
  super_admin: "Super Admin",
};

const Navbar = ({ onToggleSidebar }) => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      {/* LEFT */}
      <div className="navbar-left">
        <button
          className="navbar-toggle"
          onClick={onToggleSidebar}
          title="Toggle sidebar"
        >
          ☰
        </button>
        <Link to="/" className="navbar-brand">
          <span className="navbar-brand-icon">⬡</span>
          <span className="navbar-brand-name">AI-DAM</span>
        </Link>
      </div>

      {/* RIGHT */}
      <div className="navbar-right">
        {/* notifications — only for admin and super_admin */}
        {user?.role === "admin" || user?.role === "super_admin" ? (
          <NotificationBell />
        ) : null}

        {/* user pill */}
        <div className="navbar-user">
          <div className="navbar-avatar">
            {user?.full_name?.charAt(0).toUpperCase()}
          </div>
          <div className="navbar-user-info">
            <span className="navbar-user-name">{user?.full_name}</span>
            <span className="navbar-user-role">{ROLE_LABEL[user?.role]}</span>
          </div>
        </div>

        {/* logout */}
        <button className="navbar-logout" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
