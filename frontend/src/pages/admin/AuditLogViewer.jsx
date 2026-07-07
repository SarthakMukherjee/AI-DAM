import React, { useState, useEffect, useCallback } from "react";
import { Search, RotateCw, ChevronLeft, ChevronRight, Calendar, User, FileText, ArrowRight } from "lucide-react";
import api from "../../api/axios";
import "../../styles/AuditLogViewer.css";

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [assetFilter, setAssetFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page,
        limit,
      };
      if (actionFilter) params.action = actionFilter;
      if (userFilter) params.user_id = userFilter;
      if (assetFilter) params.asset_id = assetFilter;
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;

      const res = await api.get("/admin/audit-logs", { params });
      setLogs(res.data.items || []);
      setTotal(res.data.total || 0);
      setPages(res.data.pages || 1);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    } finally {
      setLoading(false);
    }
  }, [page, limit, actionFilter, userFilter, assetFilter, fromDate, toDate]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleReset = () => {
    setActionFilter("");
    setUserFilter("");
    setAssetFilter("");
    setFromDate("");
    setToDate("");
    setPage(1);
  };

  const renderDiff = (log) => {
    if (!log.old_value && !log.new_value) return <span className="diff-empty">—</span>;
    return (
      <div className="diff-container">
        {log.old_value && (
          <span className="diff-old" title={log.old_value}>
            {log.old_value.length > 60 ? `${log.old_value.substring(0, 60)}...` : log.old_value}
          </span>
        )}
        {log.old_value && log.new_value && (
          <span className="diff-arrow">
            <ArrowRight size={12} />
          </span>
        )}
        {log.new_value && (
          <span className="diff-new" title={log.new_value}>
            {log.new_value.length > 60 ? `${log.new_value.substring(0, 60)}...` : log.new_value}
          </span>
        )}
      </div>
    );
  };

  const getActionClass = (action) => {
    switch (action) {
      case "UPLOAD": return "action-upload";
      case "APPROVE": return "action-approve";
      case "REJECT": return "action-reject";
      case "PUBLISH": return "action-publish";
      case "RESTRICT": return "action-restrict";
      case "UNRESTRICT": return "action-unrestrict";
      case "RETIRE": return "action-retire";
      case "ARCHIVE": return "action-archive";
      case "RESOLVE_DUPLICATE": return "action-resolve";
      case "ROLE_CHANGE": return "action-role";
      default: return "action-default";
    }
  };

  return (
    <div className="audit-log-viewer">
      {/* FILTER PANEL */}
      <div className="audit-filters-panel">
        <div className="filter-grid">
          <div className="filter-group">
            <label className="filter-label">Action</label>
            <select
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
              className="filter-input-select"
            >
              <option value="">All Actions</option>
              <option value="UPLOAD">UPLOAD</option>
              <option value="SUBMIT_FOR_REVIEW">SUBMIT_FOR_REVIEW</option>
              <option value="APPROVE">APPROVE</option>
              <option value="REJECT">REJECT</option>
              <option value="PUBLISH">PUBLISH</option>
              <option value="RESTRICT">RESTRICT</option>
              <option value="UNRESTRICT">UNRESTRICT</option>
              <option value="RETIRE">RETIRE</option>
              <option value="ARCHIVE">ARCHIVE</option>
              <option value="RESOLVE_DUPLICATE">RESOLVE_DUPLICATE</option>
              <option value="ADD_PLACEMENT">ADD_PLACEMENT</option>
              <option value="ROLE_CHANGE">ROLE_CHANGE</option>
              <option value="DOMAIN_CHANGE">DOMAIN_CHANGE</option>
              <option value="DEACTIVATE_USER">DEACTIVATE_USER</option>
              <option value="REACTIVATE_USER">REACTIVATE_USER</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">User ID / Actor</label>
            <input
              type="text"
              placeholder="Filter by User ID"
              value={userFilter}
              onChange={(e) => { setUserFilter(e.target.value); setPage(1); }}
              className="filter-input-text"
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">Asset ID</label>
            <input
              type="text"
              placeholder="Filter by Asset ID"
              value={assetFilter}
              onChange={(e) => { setAssetFilter(e.target.value); setPage(1); }}
              className="filter-input-text"
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">From Date</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => { setFromDate(e.target.value); setPage(1); }}
              className="filter-input-date"
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">To Date</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => { setToDate(e.target.value); setPage(1); }}
              className="filter-input-date"
            />
          </div>
        </div>

        <div className="filter-actions">
          <button onClick={handleReset} className="reset-filters-btn">
            <RotateCw size={14} />
            Reset Filters
          </button>
        </div>
      </div>

      {/* DATA TABLE */}
      {loading ? (
        <div className="flex-center log-loader-container">
          <div className="loader" />
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state log-empty-state">
          <h3>No audit logs found</h3>
          <p>Try clearing your filters or checking a different time range.</p>
        </div>
      ) : (
        <div className="table-responsive-container">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Actor (User)</th>
                <th>Asset ID</th>
                <th>Field</th>
                <th>Changes (Old → New)</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="log-timestamp">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span className={`log-action-badge ${getActionClass(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="log-actor" title={log.user_id}>
                    <User size={12} className="inline-icon" />
                    <span>{log.user_id}</span>
                  </td>
                  <td className="log-asset-id">
                    {log.asset_id ? (
                      <a href={`/assets/${log.asset_id}`} className="asset-link-ref" target="_blank" rel="noopener noreferrer">
                        <FileText size={12} className="inline-icon" />
                        {log.asset_id.substring(0, 8)}...
                      </a>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="log-field">
                    {log.field_name ? <code>{log.field_name}</code> : <span className="text-muted">—</span>}
                  </td>
                  <td className="log-diff">
                    {renderDiff(log)}
                  </td>
                  <td className="log-ip">
                    {log.ip_address || <span className="text-muted">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* PAGINATION */}
          {pages > 1 && (
            <div className="log-pagination">
              <span className="pagination-info">
                Showing page <strong>{page}</strong> of <strong>{pages}</strong> ({total} total logs)
              </span>
              <div className="pagination-buttons">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="page-nav-btn"
                >
                  <ChevronLeft size={16} />
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(p + 1, pages))}
                  disabled={page === pages}
                  className="page-nav-btn"
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditLogViewer;
