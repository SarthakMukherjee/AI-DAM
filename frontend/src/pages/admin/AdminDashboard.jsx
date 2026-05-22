import { useState, useEffect } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";
import "../../styles/admindashboard.css";

const AdminDashboard = () => {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  // -----------------------------------
  // FETCH ALL ASSETS
  // admins see all statuses
  // -----------------------------------

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await api.get("/assets/");
        setAssets(res.data);
      } catch {
        setAssets([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  // -----------------------------------
  // DELETE ASSET
  // -----------------------------------

  const handleDelete = async (assetId) => {
    if (!window.confirm("Delete this asset? This cannot be undone.")) return;

    try {
      await api.delete(`/admin/assets/${assetId}`);
      setAssets((prev) => prev.filter((a) => a.id !== assetId));
      setSelectedAsset(null);
    } catch {
      alert("Delete failed. Please try again.");
    }
  };

  // -----------------------------------
  // FILTER
  // -----------------------------------

  const filtered =
    filter === "all" ? assets : assets.filter((a) => a.status === filter);

  const counts = {
    all: assets.length,
    draft: assets.filter((a) => a.status === "draft").length,
    approved: assets.filter((a) => a.status === "approved").length,
    rejected: assets.filter((a) => a.status === "rejected").length,
  };

  return (
    <Layout>
      <div className="admin-page">
        {/* PAGE HEADER */}
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Asset Dashboard</h1>
            <p className="admin-subtitle">
              Manage and monitor all uploaded assets
            </p>
          </div>
        </div>

        {/* STATS ROW */}
        <div className="admin-stats">
          <div className="stat-card">
            <span className="stat-value">{counts.all}</span>
            <span className="stat-label">Total Assets</span>
          </div>
          <div className="stat-card stat-card--warning">
            <span className="stat-value">{counts.draft}</span>
            <span className="stat-label">Pending Review</span>
          </div>
          <div className="stat-card stat-card--success">
            <span className="stat-value">{counts.approved}</span>
            <span className="stat-label">Approved</span>
          </div>
          <div className="stat-card stat-card--danger">
            <span className="stat-value">{counts.rejected}</span>
            <span className="stat-label">Rejected</span>
          </div>
        </div>

        {/* FILTER TABS */}
        <div className="admin-filters">
          {["all", "draft", "approved", "rejected"].map((f) => (
            <button
              key={f}
              className={`filter-tab ${filter === f ? "filter-tab--active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="filter-count">{counts[f]}</span>
            </button>
          ))}
        </div>

        {/* ASSET GRID */}
        {loading ? (
          <div className="flex-center" style={{ padding: "4rem" }}>
            <div className="loader" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <h3>No assets found</h3>
            <p>Try a different filter or upload a new asset.</p>
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

      {/* ASSET MODAL */}
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

export default AdminDashboard;
