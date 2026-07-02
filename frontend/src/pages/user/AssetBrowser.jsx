import { useState, useEffect } from "react";
import { Search, Sparkles, Brain, X, Clock, HelpCircle } from "lucide-react";

import api from "../../api/axios";

import UserLayout from "../../components/common/UserLayout";
import AssetCard from "../../components/common/AssetCard";
import AssetModal from "../../components/common/AssetModal";

import "../../styles/assetbrowser.css";

const STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "pending_review", label: "In Review" },
  { value: "approved", label: "Approved" },
  { value: "published", label: "Published" },
  { value: "restricted", label: "Restricted" },
  { value: "rejected", label: "Rejected" },
  { value: "archived", label: "Archived" }
];

const AssetBrowser = () => {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchMode, setSearchMode] = useState("hybrid");
  const [loading, setLoading] = useState(true);
  const [campaigns, setCampaigns] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [showExplanation, setShowExplanation] = useState(false);

  const [filters, setFilters] = useState({
    domain: "",
    asset_type: "",
    geography: "",
    language: "",
    status: "",
    campaign: "",
  });

  // Recent searches logic
  useEffect(() => {
    const saved = localStorage.getItem("dam_recent_searches");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) {
        setRecentSearches([]);
      }
    }
  }, []);

  const saveRecentSearch = (query) => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setRecentSearches((prev) => {
      const next = [trimmed, ...prev.filter((q) => q !== trimmed)].slice(0, 5);
      localStorage.setItem("dam_recent_searches", JSON.stringify(next));
      return next;
    });
  };

  const handleRecentClick = (query) => {
    setSearchQuery(query);
    handleSearch(null, filters, query);
  };

  const handleClearRecent = () => {
    localStorage.removeItem("dam_recent_searches");
    setRecentSearches([]);
  };

  // FETCH ASSETS
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await api.get("/assets/");
        setAssets(res.data);
        
        // Extract unique campaigns
        const uniqueCampaigns = [
          ...new Set(
            res.data
              .map((a) => a.asset_metadata?.business?.campaign)
              .filter(Boolean)
          )
        ].sort();
        setCampaigns(uniqueCampaigns);
      } catch {
        setAssets([]);
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
  }, []);

  // SEARCH
  const handleSearch = async (e, currentFilters = filters, queryOverride = null) => {
    if (e) e.preventDefault();
    const activeQuery = queryOverride !== null ? queryOverride : searchQuery;

    if (!activeQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setSearchLoading(true);
    saveRecentSearch(activeQuery);

    const endpoint =
      searchMode === "hybrid"
        ? "/api/assets/search/hybrid"
        : "/api/assets/search";

    const activeFilters = {};
    if (currentFilters.domain) activeFilters.domain = currentFilters.domain;
    if (currentFilters.asset_type) activeFilters.asset_type = currentFilters.asset_type;
    if (currentFilters.geography) activeFilters.geography = currentFilters.geography;
    if (currentFilters.language) activeFilters.language = currentFilters.language;
    if (currentFilters.status) activeFilters.status = currentFilters.status;
    if (currentFilters.campaign) activeFilters.campaign = currentFilters.campaign;

    try {
      const res = await api.post(endpoint, {
        query: activeQuery,
        limit: 20,
        approved_only: false, // Set to false to allow admins/creators searching their drafts/reviews
        filters: Object.keys(activeFilters).length > 0 ? activeFilters : null,
      });

      const mapped = res.data.results.map((r) => ({
        id: r.asset_id,
        original_filename: r.original_filename,
        storage_path: r.storage_path,
        thumbnail_path: r.thumbnail_path,
        preview_path: r.preview_path,
        mime_type: r.mime_type,
        status: r.status,
        asset_metadata: r.asset_metadata,
        score: searchMode === "hybrid" ? r.hybrid_score : r.score,
        semantic_score: typeof r.semantic_score === "number" ? r.semantic_score : null,
        keyword_score: typeof r.keyword_score === "number" ? r.keyword_score : null,
        match_explanation: r.match_explanation,
        version: r.version || 1,
        is_latest: r.is_latest !== undefined ? r.is_latest : true,
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
        query: activeQuery,
        total: 0,
        assets: [],
        mode: searchMode,
      });
    } finally {
      setSearchLoading(false);
    }
  };

  // CLEAR SEARCH
  const handleClearSearch = () => {
    setSearchQuery("");
    setSearchResults(null);
  };

  // FILTER LOGIC
  const handleFilterChange = (key, value) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    if (searchQuery.trim()) {
      handleSearch(null, updated);
    }
  };

  const handleClearFilters = () => {
    const cleared = { domain: "", asset_type: "", geography: "", language: "", status: "", campaign: "" };
    setFilters(cleared);
    if (searchQuery.trim()) {
      handleSearch(null, cleared);
    }
  };

  // DISPLAY with client-side post-filtering for responsiveness
  const isSearchMode = searchResults !== null;
  const rawList = searchResults ? searchResults.assets : assets;

  const displayAssets = rawList.filter((asset) => {
    const meta = asset.asset_metadata || {};
    const mand = meta.mandatory || {};
    const biz = meta.business || {};

    if (filters.domain && biz.domain !== filters.domain) return false;
    if (filters.asset_type && mand.asset_type !== filters.asset_type) return false;
    if (filters.geography && biz.geography !== filters.geography) return false;
    if (filters.language && biz.language !== filters.language) return false;
    if (filters.status && asset.status !== filters.status) return false;
    if (filters.campaign && biz.campaign !== filters.campaign) return false;
    return true;
  });

  return (
    <UserLayout>
      <div className="browser-page">
        {/* HEADER */}

        <div className="browser-header">
          <div className="browser-heading">
            <h1 className="browser-title">Asset Library</h1>

            <p className="browser-subtitle">
              Browse, search and download approved assets
            </p>
          </div>

          {/* SEARCH AREA */}

          <div className="browser-search-wrap">
            {/* TOGGLE */}

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
                <Sparkles size={14} />
                Hybrid
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
                <Brain size={14} />
                AI Search
              </button>
            </div>

            {/* SEARCH */}

            <form className="browser-search" onSubmit={handleSearch}>
              <div className="browser-search-icon">
                <Search size={18} />
              </div>

              <input
                type="text"
                placeholder={
                  searchMode === "hybrid"
                    ? "Search using keywords + AI understanding..."
                    : "Describe what you're looking for..."
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
                  <X size={16} />
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

            {/* RECENT SEARCHES */}
            {recentSearches.length > 0 && (
              <div className="recent-searches">
                <span className="recent-label">
                  <Clock size={12} />
                  Recent:
                </span>
                <div className="recent-badges">
                  {recentSearches.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleRecentClick(q)}
                      className="recent-badge-btn"
                    >
                      {q}
                    </button>
                  ))}
                  <button onClick={handleClearRecent} className="recent-clear-all">
                    Clear all
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* FACETED FILTERS */}
          <div className="browser-filters">
            <div className="filter-group">
              <label className="filter-label">Domain</label>
              <select
                value={filters.domain}
                onChange={(e) => handleFilterChange("domain", e.target.value)}
                className="filter-select"
              >
                <option value="">All Domains</option>
                <option value="AI">AI</option>
                <option value="Staffing">Staffing</option>
                <option value="Marketing">Marketing</option>
                <option value="Sales">Sales</option>
                <option value="Finance">Finance</option>
                <option value="HR">HR</option>
                <option value="Operations">Operations</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Tech">Tech</option>
                <option value="Design">Design</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Type</label>
              <select
                value={filters.asset_type}
                onChange={(e) => handleFilterChange("asset_type", e.target.value)}
                className="filter-select"
              >
                <option value="">All Types</option>
                <option value="image">Image</option>
                <option value="video">Video</option>
                <option value="pdf">PDF</option>
                <option value="document">Document</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Region</label>
              <select
                value={filters.geography}
                onChange={(e) => handleFilterChange("geography", e.target.value)}
                className="filter-select"
              >
                <option value="">All Regions</option>
                <option value="Global">Global</option>
                <option value="APAC">APAC</option>
                <option value="EMEA">EMEA</option>
                <option value="AMER">AMER</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Language</label>
              <select
                value={filters.language}
                onChange={(e) => handleFilterChange("language", e.target.value)}
                className="filter-select"
              >
                <option value="">All Languages</option>
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Japanese">Japanese</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Status</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange("status", e.target.value)}
                className="filter-select"
              >
                <option value="">All Statuses</option>
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Campaign</label>
              <select
                value={filters.campaign}
                onChange={(e) => handleFilterChange("campaign", e.target.value)}
                className="filter-select"
              >
                <option value="">All Campaigns</option>
                {campaigns.map((camp) => (
                  <option key={camp} value={camp}>
                    {camp}
                  </option>
                ))}
              </select>
            </div>

            {(filters.domain || filters.asset_type || filters.geography || filters.language || filters.status || filters.campaign) && (
              <button className="clear-filters-btn" onClick={handleClearFilters}>
                Reset
              </button>
            )}
          </div>
        </div>

        {/* SEARCH INFO */}

        {isSearchMode && (
          <div className="search-info-bar">
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span className="search-info-query">
                Results for <strong>"{searchResults.query}"</strong>
              </span>
              <button
                type="button"
                onClick={() => setShowExplanation(!showExplanation)}
                className="explanation-toggle-btn"
                title="How does AI rank these results?"
              >
                <HelpCircle size={15} />
              </button>
            </div>

            <span className="search-info-meta">
              {searchResults.total} result
              {searchResults.total !== 1 ? "s" : ""} ·{" "}
              {searchResults.mode === "hybrid"
                ? "Hybrid Search"
                : "AI Semantic Search"}
            </span>
          </div>
        )}

        {/* EXPLANATION DETAIL BOX */}
        {isSearchMode && showExplanation && (
          <div className="search-explanation-panel">
            <h4>💡 How Search Ranking Works</h4>
            {searchResults.mode === "hybrid" ? (
              <p>
                <strong>Hybrid Mode</strong> combines two engines:
                <ul>
                  <li><strong>Semantic Search (60% weight)</strong>: Matches files by context/meaning using AI, regardless of exact keyword matches.</li>
                  <li><strong>Keyword Search (40% weight)</strong>: Matches exact words in the filename, description, and tags.</li>
                </ul>
              </p>
            ) : (
              <p>
                <strong>AI Semantic Search Mode</strong> evaluates meaning based on AI tags, summaries, captions, and text extracted via OCR. The similarity scores represent conceptual match closeness.
              </p>
            )}
          </div>
        )}

        {/* ASSETS */}

        <section className="browser-section">
          {!isSearchMode && (
            <h2 className="browser-section-title">All Assets</h2>
          )}

          {loading && !isSearchMode ? (
            <div
              className="flex-center"
              style={{
                padding: "4rem",
              }}
            >
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
                    ? "Try a more descriptive natural-language query."
                    : "Try different keywords."
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
