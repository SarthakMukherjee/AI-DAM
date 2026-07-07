import React, { useState, useEffect } from "react";
import api from "../../api/axios";
import { Download, AlertCircle, Clock, FileText, CheckCircle, SearchX } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AnalyticsDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("missing_meta");
  
  // Data states
  const [missingMeta, setMissingMeta] = useState([]);
  const [approvalTimes, setApprovalTimes] = useState(null);
  const [searchGaps, setSearchGaps] = useState([]);
  const [unusedAssets, setUnusedAssets] = useState([]);
  
  const [loading, setLoading] = useState(false);
  
  // Fetch missing metadata
  const fetchMissingMeta = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/analytics/missing-metadata?threshold=60");
      setMissingMeta(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch approval times
  const fetchApprovalTimes = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/analytics/approval-times");
      setApprovalTimes(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch search gaps
  const fetchSearchGaps = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/analytics/search-gaps?min_results=2");
      setSearchGaps(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch unused assets
  const fetchUnusedAssets = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/analytics/unused-assets?days=90");
      setUnusedAssets(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "missing_meta") fetchMissingMeta();
    if (activeTab === "approval_times") fetchApprovalTimes();
    if (activeTab === "search_gaps") fetchSearchGaps();
    if (activeTab === "unused") fetchUnusedAssets();
  }, [activeTab]);

  const handleExport = (reportType) => {
    window.location.href = `${api.defaults.baseURL}/admin/analytics/export?report_type=${reportType}`;
  };

  return (
    <div className="analytics-dashboard">
      <div className="analytics-tabs">
        <button className={`analytics-tab ${activeTab === 'missing_meta' ? 'active' : ''}`} onClick={() => setActiveTab('missing_meta')}>Missing Metadata</button>
        <button className={`analytics-tab ${activeTab === 'approval_times' ? 'active' : ''}`} onClick={() => setActiveTab('approval_times')}>Time-to-Approval</button>
        <button className={`analytics-tab ${activeTab === 'search_gaps' ? 'active' : ''}`} onClick={() => setActiveTab('search_gaps')}>Search Gaps</button>
        <button className={`analytics-tab ${activeTab === 'unused' ? 'active' : ''}`} onClick={() => setActiveTab('unused')}>Unused Assets</button>
      </div>

      <div className="analytics-content">
        {loading ? (
           <div className="flex-center" style={{ padding: "4rem" }}><div className="loader" /></div>
        ) : (
          <>
            {activeTab === "missing_meta" && (
              <div className="analytics-section">
                <div className="analytics-header">
                  <h3>Metadata Gaps (Score < 60)</h3>
                  <button className="export-btn" onClick={() => handleExport('missing_meta')}><Download size={14}/> Export CSV</button>
                </div>
                {missingMeta.length === 0 ? (
                  <div className="empty-state">No assets with missing metadata found.</div>
                ) : (
                  <table className="analytics-table">
                    <thead><tr><th>Asset Name</th><th>Score</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>
                      {missingMeta.map(a => (
                        <tr key={a.id}>
                          <td>{a.original_filename}</td>
                          <td>
                            <div className="progress-container">
                              <div className="progress-bar" style={{width: `${a.completeness_score}%`, backgroundColor: a.completeness_score < 40 ? 'var(--danger)' : 'var(--warning)'}}></div>
                            </div>
                            <span style={{fontSize: '0.8rem'}}>{a.completeness_score}%</span>
                          </td>
                          <td><span className={`badge badge-status-${a.status}`}>{a.status}</span></td>
                          <td><button onClick={() => navigate(`/assets/${a.id}`)} className="btn-sm">Edit</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {activeTab === "approval_times" && approvalTimes && (
              <div className="analytics-section">
                <div className="analytics-header">
                  <h3>Time-to-Approval Metrics</h3>
                  <button className="export-btn" onClick={() => handleExport('approval_times')}><Download size={14}/> Export CSV</button>
                </div>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{approvalTimes.global_metrics.average_hours.toFixed(2)}h</span>
                    <span className="stat-label">Avg Time-to-Approval</span>
                  </div>
                  <div className="stat-card stat-card--success">
                    <span className="stat-value">{approvalTimes.global_metrics.total_approved}</span>
                    <span className="stat-label">Total Approved</span>
                  </div>
                  <div className="stat-card stat-card--danger">
                    <span className="stat-value">{approvalTimes.global_metrics.total_rejected}</span>
                    <span className="stat-label">Total Rejected</span>
                  </div>
                </div>
                <h4 style={{marginTop: '2rem'}}>Breakdown by Domain</h4>
                <table className="analytics-table">
                  <thead><tr><th>Domain</th><th>Average Time (Hours)</th></tr></thead>
                  <tbody>
                    {Object.entries(approvalTimes.by_domain).map(([domain, hours]) => (
                      <tr key={domain}>
                        <td>{domain}</td>
                        <td>{hours.toFixed(2)}h</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === "search_gaps" && (
              <div className="analytics-section">
                <div className="analytics-header">
                  <h3>Search Gaps (Average Results < 2)</h3>
                  <button className="export-btn" onClick={() => handleExport('search_gaps')}><Download size={14}/> Export CSV</button>
                </div>
                {searchGaps.length === 0 ? (
                  <div className="empty-state">No search gaps found.</div>
                ) : (
                  <table className="analytics-table">
                    <thead><tr><th>Search Query</th><th>Type</th><th>Times Searched</th><th>Avg Results</th></tr></thead>
                    <tbody>
                      {searchGaps.map((g, i) => (
                        <tr key={i}>
                          <td><strong>{g.query}</strong></td>
                          <td><span className="badge">{g.search_type}</span></td>
                          <td>{g.count}</td>
                          <td>{g.avg_results.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
            
            {activeTab === "unused" && (
              <div className="analytics-section">
                <div className="analytics-header">
                  <h3>Unused Assets (Over 90 days, 0 downloads/previews)</h3>
                  <button className="export-btn" onClick={() => handleExport('unused')}><Download size={14}/> Export CSV</button>
                </div>
                {unusedAssets.length === 0 ? (
                  <div className="empty-state">No unused assets found.</div>
                ) : (
                  <table className="analytics-table">
                    <thead><tr><th>Filename</th><th>Size</th><th>Created</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>
                      {unusedAssets.map(a => (
                        <tr key={a.id}>
                          <td>{a.original_filename}</td>
                          <td>{(a.file_size / 1024 / 1024).toFixed(2)} MB</td>
                          <td>{new Date(a.created_at).toLocaleDateString()}</td>
                          <td><span className={`badge badge-status-${a.status}`}>{a.status}</span></td>
                          <td><button onClick={() => navigate(`/assets/${a.id}`)} className="btn-sm">View</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
