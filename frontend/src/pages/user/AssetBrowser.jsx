import { useState, useEffect } from "react";
import api from "../../api/axios";
import UserLayout from "../../components/common/UserLayout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";
import "../../styles/assetbrowser.css";

const AssetBrowser = () => {
  const [assets, setAssets] = useState([]);
  const [mostUsed, setMostUsed] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // -----------------------------------
  // FETCH APPROVED ASSETS
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
  // FETCH MOST USED
  // silently fails for regular users
  // -----------------------------------

  useEffect(() => {
    const fetchMostUsed = async () => {
      try {
        const res = await api.get("/admin/analytics/most-used?limit=6");
        setMostUsed(res.data.top_assets || []);
      } catch {
        setMostUsed([]);
      }
    };

    fetchMostUsed();
  }, []);

  // -----------------------------------
  // SEARCH HANDLER
  // ready for semantic search integration
  // -----------------------------------

  const handleSearch = (e) => {
    e.preventDefault();
    alert("Semantic search coming soon!");
  };

  return (
    <UserLayout>
      <div className="browser-page">
        {/* PAGE HEADER */}
        <div className="browser-header">
          <div>
            <h1 className="browser-title">Asset Library</h1>
            <p className="browser-subtitle">
              Browse and download approved assets
            </p>
          </div>

          {/* SEARCH BAR */}
          <form className="browser-search" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search assets with AI... (coming soon)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="browser-search-input"
            />
            <button type="submit" className="browser-search-btn">
              Search
            </button>
          </form>
        </div>

        {/* MOST USED SECTION */}
        {mostUsed.length > 0 && (
          <section className="browser-section">
            <h2 className="browser-section-title">Most Used Assets</h2>
            <div className="browser-most-used">
              {mostUsed.map((item) => {
                const asset = assets.find((a) => a.id === item.asset_id);
                if (!asset) return null;
                return (
                  <div
                    key={item.asset_id}
                    className="most-used-card"
                    onClick={() => setSelectedAsset(asset)}
                  >
                    <div className="most-used-thumb">
                      {asset.thumbnail_path || asset.preview_path ? (
                        <img
                          src={`http://localhost:8000/assets/${asset.id}/preview`}
                          alt={item.asset_name}
                        />
                      ) : (
                        <div className="most-used-placeholder">
                          {asset.mime_type?.startsWith("video/")
                            ? "🎬"
                            : asset.mime_type === "application/pdf"
                              ? "📄"
                              : "🖼️"}
                        </div>
                      )}
                    </div>
                    <div className="most-used-info">
                      <span className="most-used-name">
                        {item.asset_name || asset.original_filename}
                      </span>
                      <span className="most-used-count">
                        {item.total_usage} uses
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ALL ASSETS */}
        <section className="browser-section">
          <h2 className="browser-section-title">All Assets</h2>

          {loading ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : assets.length === 0 ? (
            <div className="empty-state">
              <h3>No assets available</h3>
              <p>Approved assets will appear here.</p>
            </div>
          ) : (
            <div className="browser-grid">
              {assets.map((asset) => (
                <AssetCard
                  key={asset.id}
                  asset={asset}
                  onClick={() => setSelectedAsset(asset)}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {/* ASSET MODAL */}
      {selectedAsset && (
        <AssetModal
          asset={selectedAsset}
          onClose={() => setSelectedAsset(null)}
        />
      )}
    </UserLayout>
  );
};

export default AssetBrowser;
