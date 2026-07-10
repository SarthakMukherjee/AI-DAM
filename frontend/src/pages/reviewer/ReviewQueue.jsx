import { useState, useEffect } from "react";
import {
  CheckCircle2, XCircle, Eye, Clock3, ImageIcon, FileVideo, FileText,
  Folder, ShieldCheck, Globe, Lock, AlertTriangle,
} from "lucide-react";

import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/layout";
import AssetModal from "../../components/common/AssetModal";
import "../../styles/reviewqueue.css";

const TYPE_ICON = {
  "image/jpeg": ImageIcon,
  "image/png": ImageIcon,
  "video/mp4": FileVideo,
  "application/pdf": FileText,
};

const STATUS_CONFIG = {
  draft:          { label: "Draft",      cls: "badge-warning" },
  pending_review: { label: "In Review",  cls: "badge-info" },
  approved:       { label: "Approved",   cls: "badge-success" },
  rejected:       { label: "Rejected",   cls: "badge-danger" },
  published:      { label: "Published",  cls: "badge-published" },
  restricted:     { label: "Restricted", cls: "badge-restricted" },
};

const REJECTION_CATEGORIES = [
  { value: "quality",      label: "Quality Issue" },
  { value: "brand",        label: "Brand Violation" },
  { value: "legal",        label: "Legal / Compliance" },
  { value: "outdated",     label: "Outdated Content" },
  { value: "wrong_format", label: "Wrong Format" },
  { value: "other",        label: "Other" },
];

const ReviewQueue = () => {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rejectState, setRejectState] = useState({ id: null, reason: "", category: "" });
  const [actionLoading, setActionLoading] = useState(null); // stores asset ID being actioned
  const [governanceFlags, setGovernanceFlags] = useState({});

  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await api.get("/reviewer/queue");
        setAssets(res.data);
      } catch {
        setAssets([]);
      } finally {
        setLoading(false);
      }
    };
    fetchQueue();
  }, []);

  const removeFromQueue = (assetId) => setAssets((prev) => prev.filter((a) => a.id !== assetId));

  const handleApprove = async (assetId) => {
    setActionLoading(assetId);
    try {
      const flags = governanceFlags[assetId] || { website_safe: false, public_use_approved: false };
      await api.post(`/reviewer/assets/${assetId}/approve`, flags);
      removeFromQueue(assetId);
      setSelectedAsset(null);
    } catch { alert("Approval failed. Please try again."); }
    finally { setActionLoading(null); }
  };

  const handleReject = async (assetId) => {
    setActionLoading(assetId);
    try {
      await api.post(`/reviewer/assets/${assetId}/reject`, {
        reason: rejectState.reason || null,
        rejection_category: rejectState.category || null,
      });
      removeFromQueue(assetId);
      setRejectState({ id: null, reason: "", category: "" });
      setSelectedAsset(null);
    } catch { alert("Rejection failed. Please try again."); }
    finally { setActionLoading(null); }
  };

  const handlePublish = async (assetId) => {
    setActionLoading(assetId);
    try {
      await api.post(`/reviewer/assets/${assetId}/publish`, {});
      removeFromQueue(assetId);
    } catch (err) {
      alert(err?.response?.data?.detail || "Publish failed.");
    }
    finally { setActionLoading(null); }
  };

  const handleRestrict = async (assetId) => {
    const reason = prompt("Restriction reason (optional):");
    setActionLoading(assetId);
    try {
      await api.post(`/reviewer/assets/${assetId}/restrict`, { reason });
      removeFromQueue(assetId);
    } catch { alert("Restrict failed."); }
    finally { setActionLoading(null); }
  };

  return (
    <Layout>
      <div className="review-page">
        <div className="review-header">
          <div>
            <div className="dashboard-badge">
              <ShieldCheck size={14} />
              Reviewer Workspace
            </div>
            <h1 className="admin-title">Review Queue</h1>
            <p className="admin-subtitle">Moderate and validate uploaded assets</p>
          </div>
          <div className="review-queue-count">
            <Clock3 size={16} />
            <span>{assets.length} pending</span>
          </div>
        </div>

        {loading ? (
          <div className="flex-center" style={{ padding: "4rem" }}>
            <div className="loader" />
          </div>
        ) : assets.length === 0 ? (
          <div className="empty-state">
            <h3>Queue is empty</h3>
            <p>All assets have been reviewed.</p>
          </div>
        ) : (
          <div className="review-grid">
            {assets.map((asset) => {
              const assetName = asset.asset_metadata?.mandatory?.asset_name || asset.original_filename;
              const Icon = TYPE_ICON[asset.mime_type] || Folder;
              const tags = Array.isArray(asset.asset_metadata?.ai_enrichment?.ai_tags) 
                ? asset.asset_metadata.ai_enrichment.ai_tags.slice(0, 3) 
                : [];
              const rawPreview = asset.thumbnail_path || asset.preview_path || asset.storage_path || "";
              
              const isDocument = asset.mime_type === "application/pdf" || 
                                 asset.mime_type?.includes("word") || 
                                 asset.mime_type?.includes("document");
              
              const token = localStorage.getItem("access_token");
              const previewUrl = !isDocument && rawPreview 
                ? (rawPreview.startsWith("http") ? rawPreview : `${API_BASE}/assets/${asset.id}/preview${token ? `?token=${token}` : ''}`)
                : null;

              const statusCfg = STATUS_CONFIG[asset.status] || { label: asset.status, cls: "badge-warning" };
              const isRejecting = rejectState.id === asset.id;
              const isLoading = actionLoading === asset.id;
              const isMissingMeta = !asset.asset_metadata?.mandatory?.description || !asset.asset_metadata?.business?.domain;

              return (
                <div key={asset.id} className="review-card">
                  <div className="review-card-thumb" onClick={() => setSelectedAsset(asset)}>
                    {previewUrl ? (
                      <img src={previewUrl} alt={assetName} loading="lazy" />
                    ) : (
                      <div className="review-card-icon"><Icon size={52} /></div>
                    )}
                    <div className="review-card-overlay">
                      <Eye size={18} />
                      <span>View Details</span>
                    </div>
                  </div>

                  <div className="review-card-body">
                    <div className="review-card-name">{assetName}</div>

                    <div className="review-card-meta">
                      <span className={`badge ${statusCfg.cls}`}>{statusCfg.label}</span>
                      <span className="review-card-type">
                        <Icon size={14} />
                        {asset.asset_metadata?.mandatory?.asset_type || asset.mime_type}
                      </span>
                      {isMissingMeta && (
                        <span className="badge badge-warning" title="Missing required metadata">
                          <AlertTriangle size={10} /> Meta
                        </span>
                      )}
                    </div>

                    {tags.length > 0 && (
                      <div className="review-card-tags">
                        {tags.map((tag) => (
                          <span key={tag} className="asset-tag">{tag}</span>
                        ))}
                      </div>
                    )}

                    {/* REJECTION FORM */}
                    {isRejecting ? (
                      <div className="reject-inline">
                        <select
                          className="reject-select"
                          value={rejectState.category}
                          onChange={(e) => setRejectState((s) => ({ ...s, category: e.target.value }))}
                        >
                          <option value="">Select category...</option>
                          {REJECTION_CATEGORIES.map((c) => (
                            <option key={c.value} value={c.value}>{c.label}</option>
                          ))}
                        </select>
                        <input
                          type="text"
                          placeholder="Reason (optional)"
                          value={rejectState.reason}
                          onChange={(e) => setRejectState((s) => ({ ...s, reason: e.target.value }))}
                          className="reject-input"
                          autoFocus
                        />
                        <div className="reject-inline-btns">
                          <button
                            className="review-btn review-btn--danger"
                            onClick={() => handleReject(asset.id)}
                            disabled={isLoading}
                          >
                            <XCircle size={16} />
                            {isLoading ? "Rejecting..." : "Confirm Reject"}
                          </button>
                          <button
                            className="review-btn review-btn--ghost"
                            onClick={() => setRejectState({ id: null, reason: "", category: "" })}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="review-card-actions-wrapper" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        <div className="governance-toggles" style={{ display: "flex", gap: "12px", fontSize: "0.85rem", color: "#64748b" }}>
                          <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                            <input 
                              type="checkbox" 
                              checked={governanceFlags[asset.id]?.website_safe || false}
                              onChange={(e) => setGovernanceFlags(prev => ({...prev, [asset.id]: {...(prev[asset.id]||{}), website_safe: e.target.checked}}))}
                            />
                            Website Safe
                          </label>
                          <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                            <input 
                              type="checkbox" 
                              checked={governanceFlags[asset.id]?.public_use_approved || false}
                              onChange={(e) => setGovernanceFlags(prev => ({...prev, [asset.id]: {...(prev[asset.id]||{}), public_use_approved: e.target.checked}}))}
                            />
                            Public Use
                          </label>
                        </div>
                        <div className="review-card-actions">
                          <button
                            className="review-btn review-btn--approve"
                            onClick={() => handleApprove(asset.id)}
                            disabled={isLoading}
                          >
                            <CheckCircle2 size={16} />
                            {isLoading ? "..." : "Approve"}
                          </button>

                        <button
                          className="review-btn review-btn--reject"
                          onClick={() => setRejectState({ id: asset.id, reason: "", category: "" })}
                        >
                          <XCircle size={16} />
                          Reject
                        </button>

                        {asset.status === "approved" && (
                          <button
                            className="review-btn review-btn--publish"
                            onClick={() => handlePublish(asset.id)}
                            disabled={isLoading}
                          >
                            <Globe size={16} />
                            Publish
                          </button>
                        )}

                        <button
                          className="review-btn review-btn--restrict"
                          onClick={() => handleRestrict(asset.id)}
                          disabled={isLoading}
                        >
                          <Lock size={16} />
                          Restrict
                        </button>
                      </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedAsset && (
        <AssetModal asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
      )}
    </Layout>
  );
};

export default ReviewQueue;


