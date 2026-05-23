import { useState, useEffect } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import "../../styles/usermanagement.css";

const ROLES = ["user", "admin", "reviewer", "super_admin"];

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

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId);
    try {
      const res = await api.patch(`/super-admin/users/${userId}/role`, { role: newRole });
      setUsers((prev) => prev.map((u) => u.id === userId ? res.data : u));
    } catch {
      alert("Role update failed.");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDeactivate = async (userId) => {
    if (!window.confirm("Deactivate this user?")) return;
    try {
      await api.patch(`/super-admin/users/${userId}/deactivate`);
      setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, is_active: false } : u));
    } catch {
      alert("Deactivation failed.");
    }
  };

  const handleReactivate = async (userId) => {
    try {
      await api.patch(`/super-admin/users/${userId}/reactivate`);
      setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, is_active: true } : u));
    } catch {
      alert("Reactivation failed.");
    }
  };

  return (
    <Layout>
      <div className="um-page">

        <div className="admin-header">
          <div>
            <h1 className="admin-title">User Management</h1>
            <p className="admin-subtitle">{users.length} total users</p>
          </div>
        </div>

        {loading ? (
          <div className="flex-center" style={{ padding: "4rem" }}>
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
                  <tr key={user.id} className={!user.is_active ? "um-row--inactive" : ""}>
                    <td>
                      <div className="um-user-cell">
                        <div className="um-avatar">
                          {user.full_name?.charAt(0).toUpperCase()}
                        </div>
                        <span className="um-fullname">{user.full_name}</span>
                      </div>
                    </td>
                    <td className="um-email">{user.email}</td>
                    <td>
                      <select
                        className="um-role-select"
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        disabled={updatingId === user.id}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <span className={`badge ${user.is_active ? "badge-success" : "badge-danger"}`}>
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="um-date">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      {user.is_active ? (
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