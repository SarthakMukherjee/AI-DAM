import { useState, useEffect } from "react";

import { Users, ShieldCheck, UserCog, UserCheck, UserX } from "lucide-react";

import api from "../../api/axios";

import Layout from "../../components/common/Layout";

import "../../styles/usermanagement.css";

/* REMOVE super_admin */

const ROLES = ["user", "admin", "reviewer"];

const UserManagement = () => {
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);

  const [updatingId, setUpdatingId] = useState(null);

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
