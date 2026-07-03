import { useState, useEffect } from "react";
import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/layout";
import "../../styles/analytics.css";

const Analytics = () => {
  const [topAssets, setTopAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get("/admin/analytics/most-used?limit=10");

        console.log("Analytics Response:", res.data);

        setTopAssets(res.data.top_assets || []);
      } catch (err) {
        console.error("Analytics fetch failed:", err);
        setTopAssets([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const maxUsage = topAssets[0]?.total_usage || 1;

  if (loading) {
    return (
      <Layout>
        <div className="analytics-loading">Loading Analytics...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="analytics-page">
        {/* HEADER */}
        <div className="analytics-header">
          <div>
            <h1>Analytics & Usage</h1>
            <p className="analytics-subtitle">
              Monitor asset performance and top downloads across the platform
            </p>
          </div>
        </div>

        {/* MOST USED ASSETS CARD */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <h3>Most Used Assets</h3>
            <span className="analytics-badge">Top 10</span>
          </div>

          {topAssets.length === 0 ? (
            <div className="analytics-empty">
              No asset usage data recorded yet.
            </div>
          ) : (
            <div className="analytics-list">
              {topAssets.map((item, index) => {
                console.log("Analytics item:", item);

                const rawPreview =
                  item.thumbnail_url ||
                  item.preview_url ||
                  item.thumbnail_path ||
                  item.preview_path ||
                  "";
                const previewUrl = rawPreview?.startsWith("http")
                  ? rawPreview
                  : rawPreview
                    ? `${API_BASE}/assets/${item.asset_id}/preview`
                    : "";

                console.log("Preview URL:", previewUrl);

                return (
                  <div key={item.asset_id} className="analytics-row">
                    {/* RANK */}
                    <div className="analytics-rank">#{index + 1}</div>

                    {/* THUMBNAIL */}
                    <div className="analytics-thumb">
                      <img
                        src={previewUrl}
                        alt={
                          item.asset_name || item.original_filename || "Asset"
                        }
                        loading="lazy"
                        onError={(e) => {
                          console.error("Analytics image failed:", previewUrl);

                          e.target.src =
                            "https://via.placeholder.com/120x80?text=No+Image";
                        }}
                      />
                    </div>

                    {/* INFO */}
                    <div className="analytics-info">
                      <div className="analytics-top">
                        <div className="analytics-name">
                          {item.asset_name || item.original_filename}
                        </div>

                        <div className="analytics-count">
                          {item.total_usage}
                          <span> uses</span>
                        </div>
                      </div>

                      {/* BAR */}
                      <div className="analytics-bar-wrap">
                        <div
                          className="analytics-bar"
                          style={{
                            width: `${(item.total_usage / maxUsage) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Analytics;
