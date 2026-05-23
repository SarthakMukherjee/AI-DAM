import { useState, useEffect } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import "../../styles/analytics.css";

const Analytics = () => {
  const [topAssets, setTopAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get("/admin/analytics/most-used?limit=10");
        setTopAssets(res.data.top_assets || []);
      } catch {
        setTopAssets([]);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  const maxUsage = topAssets[0]?.total_usage || 1;

  return (
    <Layout>
      <div className="analytics-page">

        <div className="admin-header">
          <div>
            <h1 className="admin-title">Analytics</h1>
            <p className="admin-subtitle">Asset usage and performance overview</p>
          </div>
        </div>

        <div className="analytics-section">
          <h2 className="browser-section-title">Most Used Assets</h2>

          {loading ? (
            <div className="flex-center" style={{ padding: "4rem" }}>
              <div className="loader" />
            </div>
          ) : topAssets.length === 0 ? (
            <div className="empty-state">
              <h3>No usage data yet</h3>
              <p>Asset usage will appear here once users start downloading.</p>
            </div>
          ) : (
            <div className="analytics-list">
              {topAssets.map((item, index) => (
                <div key={item.asset_id} className="analytics-row">
                  <div className="analytics-rank">#{index + 1}</div>
                  <div className="analytics-info">
                    <div className="analytics-name">
                      {item.asset_name || item.original_filename}
                    </div>
                    <div className="analytics-bar-wrap">
                      <div
                        className="analytics-bar"
                        style={{ width: `${(item.total_usage / maxUsage) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="analytics-count">
                    {item.total_usage} <span>uses</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
};

export default Analytics;