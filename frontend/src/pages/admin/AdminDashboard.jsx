import { useState, useEffect, useCallback } from "react";
import {
  Trash2, ShieldAlert, FileText, Eye, RefreshCw,
  Merge, CheckCircle, AlertCircle, CalendarClock, Clock,
  X, ArrowRightLeft
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/Layout";
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

  // Expiring assets state
  const [expiringAssets, setExpiringAssets] = useState([]);
  const [expiringLoading, setExpiringLoading] = useState(false);
  const [checkingExpiry, setCheckingExpiry] = useState(null); // asset_id being checked

  // Resolve Duplicate modal state
  const [resolveGroup, setResolveGroup] = useState(null); // the duplicate group object
  const [resolveCanonicalId, setResolveCanonicalId] = useState("");
  const [resolveAction, setResolveAction] = useState("retire"); // "retire" | "delete"
  const [resolveMerge, setResolveMerge] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [resolveError, setResolveError] = useState("");

  // Fetch initial data (Assets and duplicates count)
  const fetchData = useCallback(async () => {
    try {
      const [assetsRes, dupsRes] = await Promise.all([
        api.get("/assets/"),
        api.get("/assets/duplicate-candidates").catch(() => ({
          data: { duplicate_groups: [] },
        })),
      ]);

      setAssets(assetsRes.data);
      setDuplicateGroups(dupsRes.data.duplicate_groups || []);
    } catch (err) {
      console.error("Failed to fetch initial admin data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

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

  // Fetch expiring assets
  const fetchExpiringAssets = async () => {
    setExpiringLoading(true);
    try {
      const res = await api.get("/admin/assets/expiring?days_threshold=30");
      setExpiringAssets(res.data.expiring_assets || []);
    } catch (err) {
      console.error("Failed to fetch expiring assets:", err);
    } finally {
      setExpiringLoading(false);
    }
  };

  // Trigger check-expiry for individual asset
  const handleCheckExpiry = async (assetId) => {
    setCheckingExpiry(assetId);
    try {
      const res = await api.post(`/admin/assets/${assetId}/check-expiry`);
      if (res.data.status_changed) {
        alert(`Asset has been automatically restricted due to expiry.`);
        fetchExpiringAssets();
      } else {
        alert(res.data.message || "No status change.");
      }
    } catch (err) {
      alert("Check expiry failed. Please try again.");
    } finally {
      setCheckingExpiry(null);
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
    if (
      !window.confirm(
        "Retire this duplicate asset? This sets its status to retired and hides it from default search.",
      )
    )
      return;
    try {
      await api.patch(`/assets/${assetId}/retire`);
      alert("Asset retired successfully.");
      fetchData();
    } catch {
      alert("Retire failed.");
    }
  };

  // -----------------------------------
  // OPEN RESOLVE MODAL
  // -----------------------------------
  const openResolveModal = (group) => {
    setResolveGroup(group);
    // Default: first asset in group is canonical
    setResolveCanonicalId(group.assets[0]?.asset_id || "");
    setResolveAction("retire");
    setResolveMerge(true);
    setResolveError("");
  };

  const closeResolveModal = () => {
    setResolveGroup(null);
    setResolveError("");
  };

  // The duplicate is the non-canonical asset in the group pair
  const getDuplicateId = () => {
    if (!resolveGroup) return null;
    return resolveGroup.assets.find((a) => a.asset_id !== resolveCanonicalId)?.asset_id || null;
  };

  // -----------------------------------
  // SUBMIT RESOLVE
  // -----------------------------------
  const handleResolve = async () => {
    const duplicateId = getDuplicateId();
    if (!resolveCanonicalId || !duplicateId) {
      setResolveError("Please select a canonical asset.");
      return;
    }

    setResolving(true);
    setResolveError("");
    try {
      await api.post("/assets/resolve-duplicate", {
        canonical_asset_id: resolveCanonicalId,
        duplicate_asset_id: duplicateId,
        action: resolveAction,
        merge_metadata: resolveMerge,
      });
      closeResolveModal();
      fetchDuplicatesOnly();
      fetchData();
    } catch (err) {
      setResolveError(
        err?.response?.data?.detail || "Failed to resolve duplicate. Please try again."
      );
    } finally {
      setResolving(false);
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
    expiring: expiringAssets.length,
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
            <button
              onClick={fetchDuplicatesOnly}
              className="refresh-dups-btn"
              disabled={duplicatesLoading}
            >
              <RefreshCw
                size={15}
                className={duplicatesLoading ? "spin" : ""}
              />
              Rescan Duplicates
            </button>
          )}
          {filter === "expiring" && (
            <button
              onClick={fetchExpiringAssets}
              className="refresh-dups-btn"
              disabled={expiringLoading}
            >
              <RefreshCw
                size={15}
                className={expiringLoading ? "spin" : ""}
              />
              Refresh
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
            <span className="filter-count filter-count--danger">
              {counts.duplicates}
            </span>
          </button>
          <button
            className={`filter-tab ${filter === "expiring" ? "filter-tab--active" : ""}`}
            onClick={() => {
              setFilter("expiring");
              fetchExpiringAssets();
            }}
          >
            <CalendarClock size={13} />
            Expiring Assets
            {counts.expiring > 0 && (
              <span className="filter-count filter-count--warning">
                {counts.expiring}
              </span>
            )}
          </button>
        </div>

        {/* MAIN CONTENT */}
        {loading ? (
          <div className="flex-center" style={{ padding: "4rem" }}>
            <div className="loader" />
          </div>

        ) : filter === "expiring" ? (
          /* ===================== EXPIRING ASSETS TAB ===================== */
          expiringLoading ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : expiringAssets.length === 0 ? (
            <div className="empty-state">
              <CheckCircle size={40} style={{ color: "var(--success)", marginBottom: "1rem" }} />
              <h3>No expiring assets</h3>
              <p>All assets are within their valid date ranges.</p>
            </div>
          ) : (
            <div className="expiring-section">
              <div className="expiring-summary-banner">
                <CalendarClock size={16} />
                <span>
                  <strong>{expiringAssets.filter(a => a.expired).length} expired</strong> and{" "}
                  <strong>{expiringAssets.filter(a => a.expiring_soon).length} expiring soon</strong>{" "}
                  within the next 30 days.
                </span>
              </div>

              <div className="expiring-list">
                {expiringAssets.map((asset) => {
                  const previewUrl = asset.thumbnail_path?.startsWith("http")
                    ? asset.thumbnail_path
                    : asset.thumbnail_path
                      ? `${API_BASE}/assets/${asset.asset_id}/preview`
                      : null;

                  return (
                    <div
                      key={asset.asset_id}
                      className={`expiring-item ${asset.expired ? "expiring-item--expired" : "expiring-item--soon"}`}
                    >
                      <div className="expiring-item-preview">
                        {previewUrl ? (
                          <img src={previewUrl} alt={asset.asset_name} />
                        ) : (
                          <div className="expiring-preview-placeholder">
                            <FileText size={28} />
                          </div>
                        )}
                      </div>

                      <div className="expiring-item-body">
                        <div className="expiring-item-name">{asset.asset_name}</div>
                        <div className="expiring-item-meta">
                          {asset.domain && (
                            <span className="badge badge-accent">{asset.domain}</span>
                          )}
                          <span className={`badge badge-status-${asset.status}`}>
                            {asset.status}
                          </span>
                          {asset.expired ? (
                            <span className="badge expiry-tag expiry-tag--expired">
                              <AlertCircle size={10} />
                              EXPIRED
                            </span>
                          ) : (
                            <span className="badge expiry-tag expiry-tag--soon">
                              <Clock size={10} />
                              {asset.days_until_expiry !== null
                                ? `${asset.days_until_expiry}d left`
                                : "EXPIRING SOON"}
                            </span>
                          )}
                        </div>
                        <div className="expiring-item-date">
                          Expiry date: <strong>{asset.expiry_date || "—"}</strong>
                        </div>
                      </div>

                      <div className="expiring-item-actions">
                        <button
                          className="dup-action-btn dup-action-btn--view"
                          onClick={() => navigate(`/assets/${asset.asset_id}`)}
                        >
                          <Eye size={13} />
                          View
                        </button>
                        <button
                          className={`expiry-check-btn ${asset.expired ? "expiry-check-btn--expired" : "expiry-check-btn--soon"}`}
                          onClick={() => handleCheckExpiry(asset.asset_id)}
                          disabled={checkingExpiry === asset.asset_id}
                        >
                          {checkingExpiry === asset.asset_id ? (
                            <RefreshCw size={13} className="spin" />
                          ) : (
                            <ShieldAlert size={13} />
                          )}
                          {asset.expired ? "Restrict Now" : "Check & Restrict"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )

        ) : filter === "duplicates" ? (
          /* ===================== DUPLICATES TAB ===================== */
          duplicatesLoading ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : duplicateGroups.length === 0 ? (
            <div className="empty-state">
              <h3>No visual duplicates found</h3>
              <p>
                Excellent! All image assets have distinct perceptual hashes.
              </p>
            </div>
          ) : (
            <div className="duplicates-section">
              <div className="duplicate-warning-banner">
                <ShieldAlert size={16} />
                <span>
                  We found {duplicateGroups.length} groups of visual duplicate
                  image files. Use <strong>Resolve Duplicate</strong> to merge metadata and
                  retire or delete the redundant copy.
                </span>
              </div>

              {duplicateGroups.map((group, gIdx) => (
                <div key={gIdx} className="duplicate-group-card">
                  <div className="dup-group-header">
                    <h4>Duplicate Group #{gIdx + 1}</h4>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <span className="dup-group-size">
                        {group.group_size} visually identical assets
                      </span>
                      {group.assets.length === 2 && (
                        <button
                          className="resolve-open-btn"
                          onClick={() => openResolveModal(group)}
                        >
                          <ArrowRightLeft size={13} />
                          Resolve Duplicate
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="dup-group-grid">
                    {group.assets.map((asset) => {
                      const previewUrl = asset.thumbnail_path?.startsWith(
                        "http",
                      )
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
                            <span
                              className="dup-item-name"
                              title={
                                asset.asset_name || asset.original_filename
                              }
                            >
                              {asset.asset_name || asset.original_filename}
                            </span>
                            <div className="dup-item-meta">
                              <span className="badge badge-accent">
                                v{asset.version}
                              </span>
                              <span
                                className={`badge badge-status-${asset.status}`}
                              >
                                {asset.status}
                              </span>
                            </div>
                            <span className="dup-item-hash">
                              pHash: <code>{asset.perceptual_hash}</code>
                            </span>
                          </div>
                          <div className="dup-item-actions">
                            <button
                              onClick={() =>
                                navigate(`/assets/${asset.asset_id}`)
                              }
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

      {/* ===================== RESOLVE DUPLICATE MODAL ===================== */}
      {resolveGroup && (
        <div className="resolve-overlay" onClick={closeResolveModal}>
          <div
            className="resolve-modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Resolve Duplicate"
          >
            {/* HEADER */}
            <div className="resolve-modal-header">
              <div className="resolve-modal-title">
                <Merge size={18} />
                <span>Resolve Duplicate</span>
              </div>
              <button className="resolve-close-btn" onClick={closeResolveModal}>
                <X size={18} />
              </button>
            </div>

            {/* BODY */}
            <div className="resolve-modal-body">
              <p className="resolve-modal-desc">
                Choose the <strong>canonical (keeper)</strong> asset. The other asset will be
                the duplicate that gets retired or deleted.
              </p>

              {/* ASSET SELECTOR */}
              <div className="resolve-asset-selector">
                {resolveGroup.assets.map((asset) => {
                  const isCanonical = asset.asset_id === resolveCanonicalId;
                  const previewUrl = asset.thumbnail_path?.startsWith("http")
                    ? asset.thumbnail_path
                    : asset.thumbnail_path
                      ? `${API_BASE}/assets/${asset.asset_id}/preview`
                      : null;
                  return (
                    <label
                      key={asset.asset_id}
                      className={`resolve-asset-option ${isCanonical ? "resolve-asset-option--selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="canonical"
                        value={asset.asset_id}
                        checked={isCanonical}
                        onChange={() => setResolveCanonicalId(asset.asset_id)}
                      />
                      <div className="resolve-asset-thumb">
                        {previewUrl ? (
                          <img src={previewUrl} alt={asset.asset_name} />
                        ) : (
                          <div className="resolve-thumb-placeholder">
                            <FileText size={24} />
                          </div>
                        )}
                      </div>
                      <div className="resolve-asset-info">
                        <span className="resolve-asset-name">
                          {asset.asset_name || asset.original_filename}
                        </span>
                        <div className="resolve-asset-badges">
                          <span className="badge badge-accent">v{asset.version}</span>
                          <span className={`badge badge-status-${asset.status}`}>{asset.status}</span>
                          {isCanonical && (
                            <span className="badge badge-success">
                              <CheckCircle size={10} /> Canonical
                            </span>
                          )}
                        </div>
                        <span className="resolve-asset-hash">
                          pHash: <code>{asset.perceptual_hash}</code>
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>

              {/* MERGE METADATA TOGGLE */}
              <label className="resolve-merge-toggle">
                <input
                  type="checkbox"
                  checked={resolveMerge}
                  onChange={(e) => setResolveMerge(e.target.checked)}
                />
                <span className="resolve-merge-label">
                  <strong>Merge metadata from duplicate into canonical</strong>
                  <small>Transfers keywords, AI tags, and detected objects to the canonical asset.</small>
                </span>
              </label>

              {/* ACTION SELECTOR */}
              <div className="resolve-action-group">
                <span className="resolve-section-label">What to do with the duplicate?</span>
                <div className="resolve-action-options">
                  <label
                    className={`resolve-action-option ${resolveAction === "retire" ? "resolve-action-option--active" : ""}`}
                  >
                    <input
                      type="radio"
                      name="action"
                      value="retire"
                      checked={resolveAction === "retire"}
                      onChange={() => setResolveAction("retire")}
                    />
                    <div>
                      <strong>Retire Duplicate</strong>
                      <small>Hides from search but keeps file on disk (soft-delete, reversible).</small>
                    </div>
                  </label>
                  <label
                    className={`resolve-action-option resolve-action-option--danger ${resolveAction === "delete" ? "resolve-action-option--active-danger" : ""}`}
                  >
                    <input
                      type="radio"
                      name="action"
                      value="delete"
                      checked={resolveAction === "delete"}
                      onChange={() => setResolveAction("delete")}
                    />
                    <div>
                      <strong>Delete Duplicate</strong>
                      <small>Permanently removes file and vector from storage and ChromaDB (irreversible).</small>
                    </div>
                  </label>
                </div>
              </div>

              {resolveError && (
                <div className="resolve-error">
                  <AlertCircle size={14} />
                  {resolveError}
                </div>
              )}
            </div>

            {/* FOOTER */}
            <div className="resolve-modal-footer">
              <button className="resolve-btn-cancel" onClick={closeResolveModal}>
                Cancel
              </button>
              <button
                className={`resolve-btn-submit ${resolveAction === "delete" ? "resolve-btn-submit--danger" : ""}`}
                onClick={handleResolve}
                disabled={resolving}
              >
                {resolving ? (
                  <RefreshCw size={14} className="spin" />
                ) : (
                  <Merge size={14} />
                )}
                {resolving ? "Resolving…" : `${resolveAction === "retire" ? "Retire" : "Delete"} & Resolve`}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default AdminDashboard;
