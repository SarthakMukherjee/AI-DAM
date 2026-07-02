import { useState, useEffect, useRef } from "react";

import {
  Users, ShieldCheck, UserCog, UserCheck, UserX,
  ChevronDown, X, Globe
} from "lucide-react";

import api from "../../api/axios";

import Layout from "../../components/common/layout";

import "../../styles/usermanagement.css";

/* Matches DomainType enum in backend metadata_enums.py */
const ALL_DOMAINS = [
  "AI",
  "Staffing",
  "Marketing",
  "Sales",
  "Finance",
  "HR",
  "Operations",
  "Healthcare",
  "Tech",
  "Design"
];

/* REMOVE super_admin from assignable roles */
const ROLES = [
  "user",
  "admin",
  "reviewer",
  "marketing_manager",
  "designer",
  "content_lead",
  "sales_user",
  "website_team",
  "external_partner"
];

/* ──────────────────────────────────────────────
   DomainDropdown — multi-select chip selector
   ────────────────────────────────────────────── */
const DomainDropdown = ({ userId, selected, onSave }) => {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open]);

  const toggle = async (domain) => {
    const current = selected || [];
    const next = current.includes(domain)
      ? current.filter((d) => d !== domain)
      : [...current, domain];

    setSaving(true);
    await onSave(userId, next);
    setSaving(false);
  };

  const removeChip = async (domain, e) => {
    e.stopPropagation();
    const next = (selected || []).filter((d) => d !== domain);
    setSaving(true);
    await onSave(userId, next);
    setSaving(false);
  };

  const clearAll = async (e) => {
    e.stopPropagation();
    setSaving(true);
    await onSave(userId, []);
    setSaving(false);
  };

  const hasSelection = selected && selected.length > 0;

  return (
    <div className="um-domain-dropdown" ref={ref}>
      {/* Trigger */}
      <button
        className={`um-domain-trigger ${open ? "um-domain-trigger--open" : ""} ${saving ? "um-domain-trigger--saving" : ""}`}
        onClick={() => setOpen(!open)}
        type="button"
      >
        {hasSelection ? (
          <span className="um-domain-chips">
            {selected.slice(0, 2).map((d) => (
              <span key={d} className="um-domain-chip">
                {d}
                <X
                  size={11}
                  className="um-domain-chip-x"
                  onClick={(e) => removeChip(d, e)}
                />
              </span>
            ))}
            {selected.length > 2 && (
              <span className="um-domain-chip um-domain-chip--more">
                +{selected.length - 2}
              </span>
            )}
          </span>
        ) : (
          <span className="um-domain-placeholder">
            <Globe size={13} />
            All Domains
          </span>
        )}
        <ChevronDown
          size={14}
          className={`um-domain-chevron ${open ? "um-domain-chevron--up" : ""}`}
        />
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="um-domain-panel">
          <div className="um-domain-panel-header">
            <span>Select Domains</span>
            {hasSelection && (
              <button className="um-domain-clear" onClick={clearAll} type="button">
                Clear all
              </button>
            )}
          </div>
          <div className="um-domain-options">
            {ALL_DOMAINS.map((domain) => {
              const checked = (selected || []).includes(domain);
              return (
                <label
                  key={domain}
                  className={`um-domain-option ${checked ? "um-domain-option--checked" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(domain)}
                    className="um-domain-checkbox"
                  />
                  <span className="um-domain-option-label">{domain}</span>
                  {checked && (
                    <span className="um-domain-check-icon">✓</span>
                  )}
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

/* ──────────────────────────────────────────────
   UserManagement page
   ────────────────────────────────────────────── */
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);

  const handleSaveDomains = async (userId, domains) => {
    try {
      const res = await api.patch(`/super-admin/users/${userId}/domains`, {
        allowed_domains: domains,
      });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId
            ? { ...u, allowed_domains: res.data.allowed_domains }
            : u
        )
      );
    } catch {
      alert("Failed to save domains.");
    }
  };

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await api.get("/super-admin/users");

        setUsers(res.data);
      } catch {
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // ROLE UPDATE

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId);

    try {
      const res = await api.patch(`/super-admin/users/${userId}/role`, {
        role: newRole,
      });

      setUsers((prev) => prev.map((u) => (u.id === userId ? res.data : u)));
    } catch {
      alert("Role update failed.");
    } finally {
      setUpdatingId(null);
    }
  };

  // DEACTIVATE

  const handleDeactivate = async (userId) => {
    if (!window.confirm("Deactivate this user?")) return;

    try {
      await api.patch(`/super-admin/users/${userId}/deactivate`);

      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId
            ? {
                ...u,
                is_active: false,
              }
            : u,
        ),
      );
    } catch {
      alert("Deactivation failed.");
    }
  };

  // REACTIVATE

  const handleReactivate = async (userId) => {
    try {
      await api.patch(`/super-admin/users/${userId}/reactivate`);

      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId
            ? {
                ...u,
                is_active: true,
              }
            : u,
        ),
      );
    } catch {
      alert("Reactivation failed.");
    }
  };

  // STATS

  const stats = {
    total: users.length,

    admins: users.filter((u) => u.role === "admin").length,

    reviewers: users.filter((u) => u.role === "reviewer").length,

    active: users.filter((u) => u.is_active).length,
  };

  return (
    <Layout>
      <div className="um-page">
        {/* HEADER */}

        <div className="um-header">
          <div>
            <div className="dashboard-badge">
              <ShieldCheck size={14} />
              User Administration
            </div>

            <h1 className="admin-title">User Management</h1>

            <p className="admin-subtitle">
              Manage users, permissions and account access
            </p>
          </div>
        </div>

        {/* STATS */}

        <div className="um-stats">
          <div className="um-stat-card">
            <div className="um-stat-icon">
              <Users size={18} />
            </div>

            <span className="um-stat-value">{stats.total}</span>

            <span className="um-stat-label">Total Users</span>
          </div>

          <div className="um-stat-card">
            <div className="um-stat-icon">
              <UserCheck size={18} />
            </div>

            <span className="um-stat-value">{stats.active}</span>

            <span className="um-stat-label">Active Users</span>
          </div>

          <div className="um-stat-card">
            <div className="um-stat-icon">
              <UserCog size={18} />
            </div>

            <span className="um-stat-value">{stats.admins}</span>

            <span className="um-stat-label">Admins</span>
          </div>

          <div className="um-stat-card">
            <div className="um-stat-icon">
              <UserX size={18} />
            </div>

            <span className="um-stat-value">{stats.reviewers}</span>

            <span className="um-stat-label">Reviewers</span>
          </div>
        </div>

        {/* TABLE */}

        {loading ? (
          <div
            className="flex-center"
            style={{
              padding: "4rem",
            }}
          >
            <div className="loader" />
          </div>
        ) : (
          <div className="um-table-wrapper">
            <table className="um-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Allowed Domains</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className={!user.is_active ? "um-row--inactive" : ""}
                  >
                    {/* USER */}

                    <td>
                      <div className="um-user-cell">
                        <div className="um-avatar">
                          {user.full_name?.charAt(0).toUpperCase()}
                        </div>

                        <div className="um-user-info">
                          <span className="um-fullname">{user.full_name}</span>

                          <span className="um-user-role">{user.role}</span>
                        </div>
                      </div>
                    </td>

                    {/* EMAIL */}

                    <td className="um-email">{user.email}</td>

                    {/* ROLE */}

                    <td>
                      {/* prevent editing super_admin */}

                      {user.role === "super_admin" ? (
                        <span className="badge badge-accent">Super Admin</span>
                      ) : (
                        <select
                          className="um-role-select"
                          value={user.role}
                          onChange={(e) =>
                            handleRoleChange(user.id, e.target.value)
                          }
                          disabled={updatingId === user.id}
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>

                    {/* ALLOWED DOMAINS */}
                    <td>
                      {user.role === "super_admin" ? (
                        <span className="badge badge-published">All</span>
                      ) : (
                        <DomainDropdown
                          userId={user.id}
                          selected={user.allowed_domains}
                          onSave={handleSaveDomains}
                        />
                      )}
                    </td>

                    {/* STATUS */}

                    <td>
                      <span
                        className={`badge ${
                          user.is_active ? "badge-success" : "badge-danger"
                        }`}
                      >
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>

                    {/* DATE */}

                    <td className="um-date">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>

                    {/* ACTIONS */}

                    <td>
                      {user.role === "super_admin" ? (
                        <span className="um-protected">Protected</span>
                      ) : user.is_active ? (
                        <button
                          className="um-btn um-btn--deactivate"
                          onClick={() => handleDeactivate(user.id)}
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          className="um-btn um-btn--activate"
                          onClick={() => handleReactivate(user.id)}
                        >
                          Reactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default UserManagement;
