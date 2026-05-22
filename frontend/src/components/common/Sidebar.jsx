import { useContext } from "react";
import { NavLink } from "react-router-dom";
import AuthContext from "../../context/AuthContext";
import "../../styles/sidebar.css";

// -----------------------------------
// NAV ITEMS PER ROLE
// -----------------------------------

const NAV_ITEMS = {
  user: [{ label: "Browse Assets", path: "/browse", icon: "◈" }],
  admin: [
    { label: "Dashboard", path: "/admin", icon: "◈" },
    { label: "Upload Asset", path: "/admin/upload", icon: "⊕" },
    { label: "Analytics", path: "/analytics", icon: "◎" },
  ],
  reviewer: [
    { label: "Review Queue", path: "/reviewer", icon: "◈" },
    { label: "Analytics", path: "/analytics", icon: "◎" },
  ],
  super_admin: [
    { label: "Dashboard", path: "/super-admin", icon: "◈" },
    { label: "User Management", path: "/super-admin/users", icon: "⊞" },
    { label: "Upload Asset", path: "/admin/upload", icon: "⊕" },
    { label: "Review Queue", path: "/reviewer", icon: "✓" },
    { label: "Analytics", path: "/analytics", icon: "◎" },
  ],
};

const Sidebar = ({ collapsed }) => {
  const { user } = useContext(AuthContext);

  const items = NAV_ITEMS[user?.role] || [];

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <nav className="sidebar-nav">
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/admin" || item.path === "/super-admin"}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "sidebar-link--active" : ""}`
            }
          >
            <span className="sidebar-icon">{item.icon}</span>
            {!collapsed && <span className="sidebar-label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
