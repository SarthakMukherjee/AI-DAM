import { useContext } from "react";

import {
  LayoutDashboard,
  Upload,
  BarChart3,
  ClipboardCheck,
  Users,
  FolderOpen,
} from "lucide-react";

import { NavLink } from "react-router-dom";

import AuthContext from "../../context/AuthContext";

import "../../styles/sidebar.css";

/* -----------------------------------
   NAV ITEMS
----------------------------------- */

const NAV_ITEMS = {
  user: [
    {
      label: "Browse Assets",
      path: "/browse",
      icon: FolderOpen,
    },
  ],

  admin: [
    {
      label: "Dashboard",
      path: "/admin",
      icon: LayoutDashboard,
    },

    {
      label: "Upload Asset",
      path: "/admin/upload",
      icon: Upload,
    },

    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
  ],

  reviewer: [
    {
      label: "Review Queue",
      path: "/reviewer",
      icon: ClipboardCheck,
    },

    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
  ],

  super_admin: [
    {
      label: "Dashboard",
      path: "/super-admin",
      icon: LayoutDashboard,
    },

    {
      label: "User Management",
      path: "/super-admin/users",
      icon: Users,
    },

    {
      label: "Upload Asset",
      path: "/admin/upload",
      icon: Upload,
    },

    {
      label: "Review Queue",
      path: "/reviewer",
      icon: ClipboardCheck,
    },

    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
  ],
};

const Sidebar = ({ collapsed }) => {
  const { user } = useContext(AuthContext);

  const items = NAV_ITEMS[user?.role] || [];

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <nav className="sidebar-nav">
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/admin" || item.path === "/super-admin"}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "sidebar-link--active" : ""}`
              }
            >
              <span className="sidebar-icon">
                <Icon size={18} />
              </span>

              {!collapsed && (
                <span className="sidebar-label">{item.label}</span>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;
