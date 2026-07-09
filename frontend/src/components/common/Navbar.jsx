import { useContext } from "react";

import { Menu, LogOut, Hexagon } from "lucide-react";

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
    <nav className="navbar glass-header">
      {/* LEFT */}

      <div className="navbar-left">
        <button
          className="navbar-toggle"
          onClick={onToggleSidebar}
          title="Toggle sidebar"
        >
          <Menu size={18} />
        </button>

        <Link to="/" className="navbar-brand">
          <div className="navbar-brand-icon">
            <Hexagon size={18} />
          </div>

          <div className="navbar-brand-text">
            <span className="navbar-brand-name">AI-DAM</span>

            <span className="navbar-brand-sub">Digital Asset Manager</span>
          </div>
        </Link>
      </div>

      {/* RIGHT */}

      <div className="navbar-right">
        {/* notifications */}

        {(user?.role === "admin" || user?.role === "super_admin") && (
          <NotificationBell />
        )}

        {/* USER */}

        <div className="navbar-user">
          <div className="navbar-avatar">
            {user?.full_name?.charAt(0).toUpperCase()}
          </div>

          <div className="navbar-user-info">
            <span className="navbar-user-name">{user?.full_name}</span>

            <span className="navbar-user-role">{ROLE_LABEL[user?.role]}</span>
          </div>
        </div>

        {/* LOGOUT */}

        <button className="navbar-logout" onClick={handleLogout}>
          <LogOut size={16} />
          <span>Sign out</span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
