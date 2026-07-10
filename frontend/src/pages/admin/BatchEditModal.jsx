import React, { useState } from "react";
import { X, CheckCircle } from "lucide-react";

const ASSET_TYPES = [
  "image", "video", "pdf", "document",
  "banner", "brochure", "case_study", "logo",
  "social_creative", "pitch_deck", "brand_guideline",
  "campaign_file", "testimonial",
];

const DOMAIN_TYPES = ["AI","Staffing","Marketing","Sales","Finance","HR","Operations","Healthcare","Tech","Design"];
const USE_CASES = ["email","presentation","website","campaign","sales","social_media","advertisment"];

const BatchEditModal = ({ item, onClose, onSave }) => {
  const [form, setForm] = useState(item.metadata);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSave = () => {
    onSave(item.id, form);
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
            <span>Edit Metadata: {item.file.name}</span>
          </div>
          <button className="resolve-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="resolve-modal-body" style={{ padding: '1rem' }}>
          <div className="upload-row" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Asset Name *</label>
              <input 
                name="asset_name" 
                value={form.asset_name || ""} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Asset Type *</label>
              <select 
                name="asset_type" 
                value={form.asset_type || "image"} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              >
                {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Description</label>
            <textarea 
              name="description" 
              value={form.description || ""} 
              onChange={handleChange} 
              rows={3}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            />
          </div>

          <div className="upload-row" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Domain</label>
              <select 
                name="domain" 
                value={form.domain || "AI"} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              >
                {DOMAIN_TYPES.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Use Case</label>
              <select 
                name="use_case" 
                value={form.use_case || "website"} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              >
                {USE_CASES.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
          </div>

          <div className="upload-row" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Campaign</label>
              <input 
                name="campaign" 
                value={form.campaign || ""} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Keywords (comma separated)</label>
              <input 
                name="keywords" 
                value={form.keywords || ""} 
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
              />
            </div>
          </div>
        </div>

        <div className="resolve-modal-footer">
          <button className="resolve-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="resolve-btn-submit" onClick={handleSave}>
            <CheckCircle size={14} /> Save Metadata
          </button>
        </div>
      </div>
    </div>
  );
};

export default BatchEditModal;
