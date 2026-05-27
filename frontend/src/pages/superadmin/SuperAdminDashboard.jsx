import { useState, useEffect } from "react";

import {
  ShieldCheck,
  Users,
  UserCog,
  ClipboardCheck,
  FolderOpen,
  CheckCircle2,
  Clock3,
  XCircle,
  ArrowRight,
} from "lucide-react";

import { Link } from "react-router-dom";

import api from "../../api/axios";

import Layout from "../../components/common/Layout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";

import "../../styles/admindashboard.css";

const SuperAdminDashboard = () => {
  const [assets, setAssets] = useState([]);

  const [users, setUsers] = useState([]);

  const [selectedAsset, setSelectedAsset] = useState(null);

  const [loading, setLoading] = useState(true);

  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetsRes, usersRes] = await Promise.all([
          api.get("/assets/"),
          api.get("/super-admin/users"),
        ]);

        setAssets(assetsRes.data);

        setUsers(usersRes.data);
      } catch {
        setAssets([]);
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // DELETE

  const handleDelete = async (assetId) => {
    if (!window.confirm("Delete this asset? This cannot be undone.")) return;

    try {
      await api.delete(`/admin/assets/${assetId}`);

      setAssets((prev) => prev.filter((a) => a.id !== assetId));

      setSelectedAsset(null);
    } catch {
      alert("Delete failed.");
    }
  };

  // FILTER

  const filtered =
    filter === "all" ? assets : assets.filter((a) => a.status === filter);

  // COUNTS

  const counts = {
    all: assets.length,

    draft: assets.filter((a) => a.status === "draft").length,

    approved: assets.filter((a) => a.status === "approved").length,

    rejected: assets.filter((a) => a.status === "rejected").length,
  };

  const userCounts = {
    total: users.length,

    admins: users.filter((u) => u.role === "admin").length,

    reviewers: users.filter((u) => u.role === "reviewer").length,

    active: users.filter((u) => u.is_active).length,
  };

  return (
    <Layout>
      <div className="admin-page">
        {/* HEADER */}

        <div className="admin-header">
          <div>
            <div className="dashboard-badge">
              <ShieldCheck size={14} />
              Super Admin
            </div>

            <h1 className="admin-title">System Dashboard</h1>

            <p className="admin-subtitle">
              Full system overview and platform management
            </p>
          </div>

          <Link to="/super-admin/users" className="dashboard-action-btn">
            <span>Manage Users</span>

            <ArrowRight size={16} />
          </Link>
        </div>

        {/* USER STATS */}

        <section className="dashboard-section">
          <div className="section-header">
            <h2>User Statistics</h2>
          </div>

          <div className="admin-stats">
            <div className="stat-card">
              <div className="stat-icon">
                <Users size={18} />
              </div>

              <span className="stat-value">{userCounts.total}</span>

              <span className="stat-label">Total Users</span>
            </div>

            <div className="stat-card stat-card--success">
              <div className="stat-icon">
                <ShieldCheck size={18} />
              </div>

              <span className="stat-value">{userCounts.active}</span>

              <span className="stat-label">Active Users</span>
            </div>

            <div className="stat-card stat-card--warning">
              <div className="stat-icon">
                <UserCog size={18} />
              </div>

              <span className="stat-value">{userCounts.admins}</span>

              <span className="stat-label">Admins</span>
            </div>

            <div className="stat-card stat-card--danger">
              <div className="stat-icon">
                <ClipboardCheck size={18} />
              </div>

              <span className="stat-value">{userCounts.reviewers}</span>

              <span className="stat-label">Reviewers</span>
            </div>
          </div>
        </section>

        {/* ASSET STATS */}

        <section className="dashboard-section">
          <div className="section-header">
            <h2>Asset Statistics</h2>
          </div>

          <div className="admin-stats">
            <div className="stat-card">
              <div className="stat-icon">
                <FolderOpen size={18} />
              </div>

              <span className="stat-value">{counts.all}</span>

              <span className="stat-label">Total Assets</span>
            </div>

            <div className="stat-card stat-card--warning">
              <div className="stat-icon">
                <Clock3 size={18} />
              </div>

              <span className="stat-value">{counts.draft}</span>

              <span className="stat-label">Pending Review</span>
            </div>

            <div className="stat-card stat-card--success">
              <div className="stat-icon">
                <CheckCircle2 size={18} />
              </div>

              <span className="stat-value">{counts.approved}</span>

              <span className="stat-label">Approved</span>
            </div>

            <div className="stat-card stat-card--danger">
              <div className="stat-icon">
                <XCircle size={18} />
              </div>

              <span className="stat-value">{counts.rejected}</span>

              <span className="stat-label">Rejected</span>
            </div>
          </div>
        </section>

        {/* FILTERS */}

        <div className="admin-filters">
          {["all", "draft", "approved", "rejected"].map((f) => (
            <button
              key={f}
              className={`filter-tab ${
                filter === f ? "filter-tab--active" : ""
              }`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}

              <span className="filter-count">{counts[f]}</span>
            </button>
          ))}
        </div>

        {/* GRID */}

        {loading ? (
          <div
            className="flex-center"
            style={{
              padding: "4rem",
            }}
          >
            <div className="loader" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <h3>No assets found</h3>

            <p>Try another filter or upload a new asset.</p>
          </div>
        ) : (
          <div className="browser-grid">
            {filtered.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                onClick={() => setSelectedAsset(asset)}
              />
            ))}
          </div>
        )}
      </div>

      {/* MODAL */}

      {selectedAsset && (
        <AssetModal
          asset={selectedAsset}
          onClose={() => setSelectedAsset(null)}
          onDelete={() => handleDelete(selectedAsset.id)}
          showDelete
        />
      )}
    </Layout>
  );
};

export default SuperAdminDashboard;
