import { useState, useEffect } from "react";

import {
  CheckCircle2,
  XCircle,
  Eye,
  Clock3,
  ImageIcon,
  FileVideo,
  FileText,
  Folder,
  ShieldCheck,
} from "lucide-react";

import api from "../../api/axios";

import Layout from "../../components/common/layout";
import AssetModal from "../../components/common/AssetModal";

import "../../styles/reviewqueue.css";

/* ICONS */

const TYPE_ICON = {
  "image/jpeg": ImageIcon,
  "image/png": ImageIcon,
  "video/mp4": FileVideo,
  "application/pdf": FileText,
};

const ReviewQueue = () => {
  const [assets, setAssets] = useState([]);

  const [selectedAsset, setSelectedAsset] = useState(null);

  const [loading, setLoading] = useState(true);

  const [rejectReason, setRejectReason] = useState("");

  const [rejectingId, setRejectingId] = useState(null);

  const [actionLoading, setActionLoading] = useState(false);

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

  // APPROVE

  const handleApprove = async (assetId) => {
    setActionLoading(true);

    try {
      await api.post(`/reviewer/assets/${assetId}/approve`);

      setAssets((prev) => prev.filter((a) => a.id !== assetId));

      setSelectedAsset(null);
    } catch {
      alert("Approval failed. Please try again.");
    } finally {
      setActionLoading(false);
    }
  };

  // REJECT

  const handleReject = async (assetId) => {
    setActionLoading(true);

    try {
      await api.post(`/reviewer/assets/${assetId}/reject`, {
        reason: rejectReason || null,
      });

      setAssets((prev) => prev.filter((a) => a.id !== assetId));

      setRejectingId(null);

      setRejectReason("");

      setSelectedAsset(null);
    } catch {
      alert("Rejection failed. Please try again.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <Layout>
      <div className="review-page">
        {/* HEADER */}

        <div className="review-header">
          <div>
            <div className="dashboard-badge">
              <ShieldCheck size={14} />
              Reviewer Workspace
            </div>

            <h1 className="admin-title">Review Queue</h1>

            <p className="admin-subtitle">
              Moderate and validate uploaded assets
            </p>
          </div>

          <div className="review-queue-count">
            <Clock3 size={16} />

            <span>{assets.length} pending</span>
          </div>
        </div>

        {/* CONTENT */}

        {loading ? (
          <div
            className="flex-center"
            style={{
              padding: "4rem",
            }}
          >
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
              const assetName =
                asset.asset_metadata?.mandatory?.asset_name ||
                asset.original_filename;

              const Icon = TYPE_ICON[asset.mime_type] || Folder;

              const tags =
                asset.asset_metadata?.ai_enrichment?.ai_tags?.slice(0, 3) || [];

              return (
                <div key={asset.id} className="review-card">
                  {/* THUMB */}

                  <div
                    className="review-card-thumb"
                    onClick={() => setSelectedAsset(asset)}
                  >
                    {asset.thumbnail_path || asset.preview_path ? (
                      <img
                        src={`http://localhost:8000/assets/${asset.id}/preview`}
                        alt={assetName}
                      />
                    ) : (
                      <div className="review-card-icon">
                        <Icon size={52} />
                      </div>
                    )}

                    <div className="review-card-overlay">
                      <Eye size={18} />

                      <span>View Details</span>
                    </div>
                  </div>

                  {/* BODY */}

                  <div className="review-card-body">
                    <div className="review-card-name">{assetName}</div>

                    <div className="review-card-meta">
                      <span className="badge badge-warning">draft</span>

                      <span className="review-card-type">
                        <Icon size={14} />

                        {asset.mime_type}
                      </span>
                    </div>

                    {/* TAGS */}

                    {tags.length > 0 && (
                      <div className="review-card-tags">
                        {tags.map((tag) => (
                          <span key={tag} className="asset-tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* ACTIONS */}

                    {rejectingId === asset.id ? (
                      <div className="reject-inline">
                        <input
                          type="text"
                          placeholder="Reason (optional)"
                          value={rejectReason}
                          onChange={(e) => setRejectReason(e.target.value)}
                          className="reject-input"
                          autoFocus
                        />

                        <div className="reject-inline-btns">
                          <button
                            className="review-btn review-btn--danger"
                            onClick={() => handleReject(asset.id)}
                            disabled={actionLoading}
                          >
                            <XCircle size={16} />
                            Confirm Reject
                          </button>

                          <button
                            className="review-btn review-btn--ghost"
                            onClick={() => {
                              setRejectingId(null);

                              setRejectReason("");
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="review-card-actions">
                        <button
                          className="review-btn review-btn--approve"
                          onClick={() => handleApprove(asset.id)}
                          disabled={actionLoading}
                        >
                          <CheckCircle2 size={16} />
                          Approve
                        </button>

                        <button
                          className="review-btn review-btn--reject"
                          onClick={() => setRejectingId(asset.id)}
                        >
                          <XCircle size={16} />
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MODAL */}

      {selectedAsset && (
        <AssetModal
          asset={selectedAsset}
          onClose={() => setSelectedAsset(null)}
        />
      )}
    </Layout>
  );
};

export default ReviewQueue;
