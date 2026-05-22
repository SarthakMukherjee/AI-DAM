import { useEffect, useState } from "react";
import api from "../../api/axios";

import Layout from "../../components/common/layout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";

const ReviewQueue = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  const [selectedAsset, setSelectedAsset] = useState(null);

  const [rejectReason, setRejectReason] = useState("");
  const [showRejectBox, setShowRejectBox] = useState(false);

  // ====================================
  // FETCH REVIEW QUEUE
  // ====================================

  useEffect(() => {
    let mounted = true;

    const loadQueue = async () => {
      try {
        const res = await api.get("/reviewer/queue");

        if (mounted) {
          setAssets(res.data);
        }
      } catch (err) {
        console.error(err);

        if (mounted) {
          alert("Failed to load review queue");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadQueue();

    return () => {
      mounted = false;
    };
  }, []);

  // ====================================
  // APPROVE
  // ====================================

  const approveAsset = async (assetId) => {
    try {
      await api.post(`/reviewer/assets/${assetId}/approve`);

      setAssets((prev) => prev.filter((a) => a.id !== assetId));

      setSelectedAsset(null);

      alert("Asset approved");
    } catch (err) {
      console.error(err);
      alert("Failed to approve asset");
    }
  };

  // ====================================
  // REJECT
  // ====================================

  const rejectAsset = async () => {
    if (!selectedAsset) return;

    try {
      await api.post(`/reviewer/assets/${selectedAsset.id}/reject`, {
        reason: rejectReason,
      });

      setAssets((prev) => prev.filter((a) => a.id !== selectedAsset.id));

      setSelectedAsset(null);
      setShowRejectBox(false);
      setRejectReason("");

      alert("Asset rejected");
    } catch (err) {
      console.error(err);
      alert("Failed to reject asset");
    }
  };

  // ====================================
  // LOADING
  // ====================================

  if (loading) {
    return (
      <Layout>
        <div className="loader-screen">
          <div className="loader" />
        </div>
      </Layout>
    );
  }

  // ====================================
  // UI
  // ====================================

  return (
    <Layout>
      <div className="dashboard-page">
        <div className="dashboard-header">
          <h1>Review Queue</h1>
          <p>Pending assets awaiting approval or rejection</p>
        </div>

        {assets.length === 0 ? (
          <div className="empty-state">No assets pending review</div>
        ) : (
          <div className="asset-grid">
            {assets.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                onClick={() => setSelectedAsset(asset)}
              />
            ))}
          </div>
        )}

        {/* ====================================
            MODAL
        ==================================== */}

        {selectedAsset && (
          <>
            <AssetModal
              asset={selectedAsset}
              onClose={() => {
                setSelectedAsset(null);
                setShowRejectBox(false);
              }}
            />

            <div
              style={{
                display: "flex",
                gap: "12px",
                marginTop: "20px",
                justifyContent: "center",
              }}
            >
              <button
                className="modal-btn modal-btn-primary"
                onClick={() => approveAsset(selectedAsset.id)}
              >
                ✅ Approve
              </button>

              <button
                className="modal-btn modal-btn-danger"
                onClick={() => setShowRejectBox(true)}
              >
                ❌ Reject
              </button>
            </div>

            {/* ====================================
                REJECT BOX
            ==================================== */}

            {showRejectBox && (
              <div
                style={{
                  marginTop: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  alignItems: "center",
                }}
              >
                <textarea
                  placeholder="Enter rejection reason..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  rows={4}
                  style={{
                    width: "400px",
                    padding: "12px",
                    borderRadius: "10px",
                  }}
                />

                <button
                  className="modal-btn modal-btn-danger"
                  onClick={rejectAsset}
                >
                  Confirm Reject
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};

export default ReviewQueue;
