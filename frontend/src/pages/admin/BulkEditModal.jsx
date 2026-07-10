import React, { useState } from "react";
import { X, CheckCircle, AlertCircle } from "lucide-react";
import api from "../../api/axios";

const STATUS_OPTIONS = ["draft", "pending_review", "approved", "rejected", "restricted", "archived"];
const DOMAIN_TYPES = ["AI","Staffing","Marketing","Sales","Finance","HR","Operations","Healthcare","Tech","Design"];

const BulkEditModal = ({ selectedAssetIds, onClose, onComplete }) => {
  const [form, setForm] = useState({
    status: "",
    domain: "",
    geographic_restrictions: "",
    platform_restrictions: "",
    model_release_status: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    if (selectedAssetIds.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const payload = {
        asset_ids: selectedAssetIds,
        metadata_updates: {}
      };
      
      if (form.status) payload.status = form.status;
      if (form.geographic_restrictions) payload.geographic_restrictions = form.geographic_restrictions.split(",").map(s => s.trim()).filter(Boolean);
      if (form.platform_restrictions) payload.platform_restrictions = form.platform_restrictions.split(",").map(s => s.trim()).filter(Boolean);
      if (form.model_release_status) payload.model_release_status = form.model_release_status;
      
      if (form.domain) {
        payload.metadata_updates.business = { domain: form.domain };
      }
      
      // Send bulk edit request
      await api.put('/assets/bulk-edit', payload);
      
      onComplete();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Bulk edit failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="resolve-overlay" onClick={onClose} style={{ zIndex: 1000 }}>
      <div 
        className="resolve-modal" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '600px', width: '90%', maxHeight: '90vh', overflowY: 'auto' }}
      >
        <div className="resolve-modal-header">
          <div className="resolve-modal-title">
            <span>Bulk Edit {selectedAssetIds.length} Assets</span>
          </div>
          <button className="resolve-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="resolve-modal-body" style={{ padding: '1rem' }}>
          <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1rem' }}>
            Leave a field blank if you do not want to change it.
          </p>
          
          {error && (
            <div style={{ padding: '0.75rem', background: '#fef2f2', color: '#b91c1c', borderRadius: '6px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div className="upload-row" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Status</label>
              <select 
                name="status" 
                value={form.status} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
              >
                <option value="">-- No Change --</option>
                {STATUS_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Domain</label>
              <select 
                name="domain" 
                value={form.domain} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
              >
                <option value="">-- No Change --</option>
                {DOMAIN_TYPES.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Geographic Restrictions (comma separated)</label>
            <input 
              name="geographic_restrictions" 
              value={form.geographic_restrictions} 
              onChange={handleChange} 
              placeholder="e.g. US, EU, None"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Platform Restrictions (comma separated)</label>
            <input 
              name="platform_restrictions" 
              value={form.platform_restrictions} 
              onChange={handleChange} 
              placeholder="e.g. Meta, YouTube"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Model Release Status</label>
            <select 
              name="model_release_status" 
              value={form.model_release_status} 
              onChange={handleChange}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
            >
              <option value="">-- No Change --</option>
              <option value="Not Required">Not Required</option>
              <option value="Required - Pending">Required - Pending</option>
              <option value="Required - Cleared">Required - Cleared</option>
            </select>
          </div>

        </div>

        <div className="resolve-modal-footer">
          <button className="resolve-btn resolve-btn--cancel" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="resolve-btn resolve-btn--confirm" onClick={handleSave} disabled={loading}>
            {loading ? "Applying..." : "Apply Bulk Edit"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BulkEditModal;
