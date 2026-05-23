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
  const [searchResults, setSearchResults] = useState(null); // null = no search done yet
  const [searchLoading, setSearchLoading] = useState(false);
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
  // SEMANTIC SEARCH
  // -----------------------------------

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setSearchLoading(true);

    try {
      const res = await api.post("/api/assets/search", {
        query: searchQuery,
        limit: 20,
        approved_only: true,
      });

      // map search results to same shape as asset list
      // search returns asset_id instead of id
      const mapped = res.data.results.map((r) => ({
        id: r.asset_id,
        original_filename: r.original_filename,
        storage_path: r.storage_path,
        thumbnail_path: r.thumbnail_path,
        preview_path: r.preview_path,
        mime_type: r.mime_type,
        status: r.status,
        asset_metadata: r.asset_metadata,
        score: r.score,
        version: 1,
        is_latest: true,
      }));

      setSearchResults({
        query: res.data.query,
        total: res.data.total,
        assets: mapped,
      });

    } catch {
      setSearchResults({ query: searchQuery, total: 0, assets: [] });
    } finally {
      setSearchLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setSearchResults(null);
  };

  // -----------------------------------
  // DISPLAY — search results or all assets
  // -----------------------------------

  const displayAssets = searchResults ? searchResults.assets : assets;
  const isSearchMode = searchResults !== null;

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
              placeholder="Search assets with AI..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="browser-search-input"
            />
            {isSearchMode && (
              <button
                type="button"
                className="browser-clear-btn"
                onClick={handleClearSearch}
              >
                Clear
              </button>
            )}
            <button
              type="submit"
              className="browser-search-btn"
              disabled={searchLoading}
            >
              {searchLoading ? <span className="btn-loader" style={{ width: 14, height: 14, borderWidth: 2 }} /> : "Search"}
            </button>
          </form>
        </div>

        {/* MOST USED — only shown when not searching */}
        {!isSearchMode && mostUsed.length > 0 && (
          <section className="browser-section">
            <h2 className="browser-section-title">🔥 Most Used Assets</h2>
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
                          {asset.mime_type?.startsWith("video/") ? "🎬"
                            : asset.mime_type === "application/pdf" ? "📄"
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

        {/* RESULTS SECTION */}
        <section className="browser-section">

          {isSearchMode ? (
            <div className="browser-search-header">
              <h2 className="browser-section-title">
                Search results for "{searchResults.query}"
              </h2>
              <span className="browser-search-count">
                {searchResults.total} result{searchResults.total !== 1 ? "s" : ""}
              </span>
            </div>
          ) : (
            <h2 className="browser-section-title">All Assets</h2>
          )}

          {loading && !isSearchMode ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : displayAssets.length === 0 ? (
            <div className="empty-state">
              <h3>{isSearchMode ? "No results found" : "No assets available"}</h3>
              <p>
                {isSearchMode
                  ? "Try a different search query."
                  : "Approved assets will appear here."}
              </p>
            </div>
          ) : (
            <div className="browser-grid">
              {displayAssets.map((asset) => (
                <AssetCard
                  key={asset.id}
                  asset={asset}
                  onClick={() => setSelectedAsset(asset)}
                  score={asset.score}
                />
              ))}
            </div>
          )}

        </section>

      </div>

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