import { useState, useEffect } from "react";
import { Trash2, ShieldAlert, FileText, Eye, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/layout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";
import "../../styles/admindashboard.css";

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [duplicateGroups, setDuplicateGroups] = useState([]);
  const [duplicatesLoading, setDuplicatesLoading] = useState(false);

  // Fetch initial data (Assets and duplicates count)
  const fetchData = async () => {
    setLoading(true);
    try {
      const [assetsRes, dupsRes] = await Promise.all([
        api.get("/assets/"),
        api.get("/assets/duplicate-candidates").catch(() => ({ data: { duplicate_groups: [] } }))
      ]);
      setAssets(assetsRes.data);
      setDuplicateGroups(dupsRes.data.duplicate_groups || []);
    } catch (err) {
      console.error("Failed to fetch initial admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch duplicates explicitly when tab selected
  const fetchDuplicatesOnly = async () => {
    setDuplicatesLoading(true);
    try {
      const res = await api.get("/assets/duplicate-candidates");
      setDuplicateGroups(res.data.duplicate_groups || []);
    } catch (err) {
      console.error(err);
    } finally {
      setDuplicatesLoading(false);
    }
  };

  // -----------------------------------
  // DELETE ASSET
  // -----------------------------------
  const handleDelete = async (assetId) => {
    if (!window.confirm("Delete this asset? This cannot be undone.")) return;
    try {
      await api.delete(`/admin/assets/${assetId}`);
      setAssets((prev) => prev.filter((a) => a.id !== assetId));
      setSelectedAsset(null);
      fetchDuplicatesOnly();
    } catch {
      alert("Delete failed. Please try again.");
    }
  };

  // -----------------------------------
  // RETIRE ASSET (SOFT DELETE)
  // -----------------------------------
  const handleRetire = async (assetId) => {
    if (!window.confirm("Retire this duplicate asset? This sets its status to retired and hides it from default search.")) return;
    try {
      await api.patch(`/assets/${assetId}/retire`);
      alert("Asset retired successfully.");
      fetchData();
    } catch {
      alert("Retire failed.");
    }
  };

  const filtered =
    filter === "all" ? assets : assets.filter((a) => a.status === filter);

  const counts = {
    all: assets.length,
    draft: assets.filter((a) => a.status === "draft").length,
    approved: assets.filter((a) => a.status === "approved").length,
    rejected: assets.filter((a) => a.status === "rejected").length,
    duplicates: duplicateGroups.length,
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
          {filter === "duplicates" && (
            <button onClick={fetchDuplicatesOnly} className="refresh-dups-btn" disabled={duplicatesLoading}>
              <RefreshCw size={15} className={duplicatesLoading ? "spin" : ""} />
              Rescan Duplicates
            </button>
          )}
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
          <button
            className={`filter-tab ${filter === "duplicates" ? "filter-tab--active" : ""}`}
            onClick={() => setFilter("duplicates")}
          >
            Duplicates Scan
            <span className="filter-count filter-count--danger">{counts.duplicates}</span>
          </button>
        </div>

        {/* ASSET CONTENT OR DUPLICATES */}
        {loading ? (
          <div className="flex-center" style={{ padding: "4rem" }}>
            <div className="loader" />
          </div>
        ) : filter === "duplicates" ? (
          duplicatesLoading ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : duplicateGroups.length === 0 ? (
            <div className="empty-state">
              <h3>No visual duplicates found</h3>
              <p>Excellent! All image assets have distinct perceptual hashes.</p>
            </div>
          ) : (
            <div className="duplicates-section">
              <div className="duplicate-warning-banner">
                <ShieldAlert size={16} />
                <span>We found {duplicateGroups.length} groups of visual duplicate image files. Recommend deleting or retiring outdated duplicates to save space and clean up search context.</span>
              </div>

              {duplicateGroups.map((group, gIdx) => (
                <div key={gIdx} className="duplicate-group-card">
                  <div className="dup-group-header">
                    <h4>Duplicate Group #{gIdx + 1}</h4>
                    <span className="dup-group-size">{group.group_size} visually identical assets</span>
                  </div>

                  <div className="dup-group-grid">
                    {group.assets.map((asset) => {
                      const previewUrl = asset.thumbnail_path?.startsWith("http")
                        ? asset.thumbnail_path
                        : asset.thumbnail_path
                          ? `${API_BASE}/assets/${asset.asset_id}/preview`
                          : null;
                      return (
                        <div key={asset.asset_id} className="dup-item-card">
                          <div className="dup-item-preview">
                            {previewUrl ? (
                              <img src={previewUrl} alt={asset.asset_name} />
                            ) : (
                              <div className="dup-preview-placeholder">
                                <FileText size={32} />
                              </div>
                            )}
                          </div>
                          <div className="dup-item-details">
                            <span className="dup-item-name" title={asset.asset_name || asset.original_filename}>
                              {asset.asset_name || asset.original_filename}
                            </span>
                            <div className="dup-item-meta">
                              <span className="badge badge-accent">v{asset.version}</span>
                              <span className={`badge badge-status-${asset.status}`}>{asset.status}</span>
                            </div>
                            <span className="dup-item-hash">pHash: <code>{asset.perceptual_hash}</code></span>
                          </div>
                          <div className="dup-item-actions">
                            <button
                              onClick={() => navigate(`/assets/${asset.asset_id}`)}
                              className="dup-action-btn dup-action-btn--view"
                              title="View details"
                            >
                              <Eye size={14} />
                              View Details
                            </button>
                            {asset.status !== "retired" && (
                              <button
                                onClick={() => handleRetire(asset.asset_id)}
                                className="dup-action-btn dup-action-btn--retire"
                                title="Retire duplicate"
                              >
                                Retire
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(asset.asset_id)}
                              className="dup-action-btn dup-action-btn--delete"
                              title="Permanently delete"
                            >
                              <Trash2 size={14} />
                              Delete
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )
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
          onArchive={(id) => {
            setAssets((prev) => prev.filter((a) => a.id !== id));
            setSelectedAsset(null);
          }}
          showDelete
        />
      )}
    </Layout>
  );
};

export default AdminDashboard;
