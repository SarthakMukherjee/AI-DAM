import { useState, useEffect } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import AssetModal from "../../components/common/AssetModal";
import "../../styles/reviewqueue.css";

const TYPE_ICON = {
  "image/jpeg": "🖼️",
  "image/png": "🖼️",
  "video/mp4": "🎬",
  "application/pdf": "📄",
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

        <div className="admin-header">
          <div>
            <h1 className="admin-title">Review Queue</h1>
            <p className="admin-subtitle">
              {assets.length} asset{assets.length !== 1 ? "s" : ""} pending review
            </p>
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
              const assetName =
                asset.asset_metadata?.mandatory?.asset_name ||
                asset.original_filename;
              const icon = TYPE_ICON[asset.mime_type] || "📁";
              const tags =
                asset.asset_metadata?.ai_enrichment?.ai_tags?.slice(0, 3) || [];

              return (
                <div key={asset.id} className="review-card">

                  <div className="review-card-thumb" onClick={() => setSelectedAsset(asset)}>
                    {asset.thumbnail_path || asset.preview_path ? (
                      <img src={`http://localhost:8000/assets/${asset.id}/preview`} alt={assetName} />
                    ) : (
                      <div className="review-card-icon">{icon}</div>
                    )}
                    <div className="review-card-overlay"><span>View Details</span></div>
                  </div>

                  <div className="review-card-body">
                    <div className="review-card-name">{assetName}</div>
                    <div className="review-card-meta">
                      <span className="badge badge-warning">draft</span>
                      <span className="review-card-type">{icon} {asset.mime_type}</span>
                    </div>

                    {tags.length > 0 && (
                      <div className="review-card-tags">
                        {tags.map((tag) => (
                          <span key={tag} className="asset-tag">{tag}</span>
                        ))}
                      </div>
                    )}

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
                          <button className="review-btn review-btn--danger" onClick={() => handleReject(asset.id)} disabled={actionLoading}>
                            Confirm Reject
                          </button>
                          <button className="review-btn review-btn--ghost" onClick={() => { setRejectingId(null); setRejectReason(""); }}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="review-card-actions">
                        <button className="review-btn review-btn--approve" onClick={() => handleApprove(asset.id)} disabled={actionLoading}>
                          ✓ Approve
                        </button>
                        <button className="review-btn review-btn--reject" onClick={() => setRejectingId(asset.id)}>
                          ✕ Reject
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

      {selectedAsset && (
        <AssetModal asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
      )}

    </Layout>
  );
};

export default ReviewQueue;