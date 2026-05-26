import { useState, useEffect } from "react";
import api from "../../api/axios";

import UserLayout from "../../components/common/UserLayout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";

import "../../styles/assetbrowser.css";

const AssetBrowser = () => {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);

  const [searchLoading, setSearchLoading] = useState(false);

  const [searchMode, setSearchMode] = useState("hybrid");

  const [loading, setLoading] = useState(true);

  // ---------------------------------------------------
  // FETCH ASSETS
  // ---------------------------------------------------

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

  // ---------------------------------------------------
  // SEARCH
  // ---------------------------------------------------

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setSearchLoading(true);

    const endpoint =
      searchMode === "hybrid"
        ? "/api/assets/search/hybrid"
        : "/api/assets/search";

    try {
      const res = await api.post(endpoint, {
        query: searchQuery,
        limit: 20,
        approved_only: true,
      });

      console.log("SEARCH RESPONSE", res.data);

      const mapped = res.data.results.map((r) => ({
        id: r.asset_id,

        original_filename: r.original_filename,

        storage_path: r.storage_path,

        thumbnail_path: r.thumbnail_path,

        preview_path: r.preview_path,

        mime_type: r.mime_type,

        status: r.status,

        asset_metadata: r.asset_metadata,

        // ---------------------------------
        // MAIN SCORE
        // ---------------------------------

        score: searchMode === "hybrid" ? r.hybrid_score : r.score,

        // ---------------------------------
        // HYBRID BREAKDOWN
        // ---------------------------------

        semantic_score:
          typeof r.semantic_score === "number" ? r.semantic_score : null,

        keyword_score:
          typeof r.keyword_score === "number" ? r.keyword_score : null,

        version: 1,
        is_latest: true,
      }));

      setSearchResults({
        query: res.data.query,

        total: res.data.total,

        assets: mapped,

        mode: searchMode,
      });
    } catch (err) {
      console.error(err);

      setSearchResults({
        query: searchQuery,
        total: 0,
        assets: [],
        mode: searchMode,
      });
    } finally {
      setSearchLoading(false);
    }
  };

  // ---------------------------------------------------
  // CLEAR SEARCH
  // ---------------------------------------------------

  const handleClearSearch = () => {
    setSearchQuery("");
    setSearchResults(null);
  };

  // ---------------------------------------------------
  // DISPLAY
  // ---------------------------------------------------

  const displayAssets = searchResults ? searchResults.assets : assets;

  const isSearchMode = searchResults !== null;

  return (
    <UserLayout>
      <div className="browser-page">
        {/* HEADER */}
        <div className="browser-header">
          <div>
            <h1 className="browser-title">Asset Library</h1>

            <p className="browser-subtitle">
              Browse and download approved assets
            </p>
          </div>

          {/* SEARCH */}
          <div className="browser-search-wrap">
            {/* MODE */}
            <div className="search-mode-toggle">
              <button
                type="button"
                className={`search-mode-btn ${
                  searchMode === "hybrid" ? "search-mode-btn--active" : ""
                }`}
                onClick={() => {
                  setSearchMode("hybrid");
                  setSearchResults(null);
                }}
              >
                ⚡ Hybrid
              </button>

              <button
                type="button"
                className={`search-mode-btn ${
                  searchMode === "semantic" ? "search-mode-btn--active" : ""
                }`}
                onClick={() => {
                  setSearchMode("semantic");
                  setSearchResults(null);
                }}
              >
                🧠 AI Search
              </button>
            </div>

            {/* FORM */}
            <form className="browser-search" onSubmit={handleSearch}>
              <input
                type="text"
                placeholder={
                  searchMode === "hybrid"
                    ? "Hybrid search — keyword + AI..."
                    : "AI semantic search..."
                }
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
                {searchLoading ? "Searching..." : "Search"}
              </button>
            </form>
          </div>
        </div>

        {/* SEARCH INFO */}
        {isSearchMode && (
          <div className="search-info-bar">
            <span className="search-info-query">
              Results for <strong>"{searchResults.query}"</strong>
            </span>

            <span className="search-info-meta">
              {searchResults.total} result
              {searchResults.total !== 1 ? "s" : ""}
              &nbsp;·&nbsp;
              {searchResults.mode === "hybrid"
                ? "⚡ hybrid search"
                : "🧠 AI semantic search"}
            </span>
          </div>
        )}

        {/* ASSETS */}
        <section className="browser-section">
          {!isSearchMode && (
            <h2 className="browser-section-title">All Assets</h2>
          )}

          {loading && !isSearchMode ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : displayAssets.length === 0 ? (
            <div className="empty-state">
              <h3>
                {isSearchMode
                  ? `No ${searchResults.mode} results found`
                  : "No assets available"}
              </h3>

              <p>
                {isSearchMode
                  ? searchResults.mode === "semantic"
                    ? "Try a descriptive natural-language query."
                    : "Try another keyword."
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
                  semanticScore={asset.semantic_score}
                  keywordScore={asset.keyword_score}
                  searchMode={searchResults?.mode}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {/* MODAL */}
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
