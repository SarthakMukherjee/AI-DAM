import { useState } from "react";
import { X, Copy, Check, Link as LinkIcon, Shield, Clock, CheckCircle } from "lucide-react";
import api from "../../api/axios";

const ShareModal = ({ asset, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [expiresInDays, setExpiresInDays] = useState(7);
  const [password, setPassword] = useState("");
  
  const [generatedLink, setGeneratedLink] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        asset_id: asset.id || asset.asset_id,
        expires_in_days: expiresInDays || null,
        password: password || null
      };
      
      const res = await api.post('/shared-links/', payload);
      
      // Construct the full URL
      const shareUrl = `${window.location.origin}/share/${res.data.token}`;
      setGeneratedLink(shareUrl);
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to generate link");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (generatedLink) {
      navigator.clipboard.writeText(generatedLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="resolve-overlay" onClick={onClose} style={{ zIndex: 1100, display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'rgba(0,0,0,0.6)' }}>
      <div 
        className="resolve-modal" 
        onClick={(e) => e.stopPropagation()}
        style={{ width: '90%', maxWidth: '500px', background: 'var(--surface)', borderRadius: '8px', overflow: 'hidden' }}
      >
        <div className="resolve-modal-header" style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="resolve-modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '600' }}>
            <LinkIcon size={18} />
            Share Asset Externally
          </div>
          <button className="resolve-close-btn" onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <X size={18} />
          </button>
        </div>

        <div className="resolve-modal-body" style={{ padding: '1.5rem' }}>
          {!generatedLink ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Generate a secure link to share <strong>{asset.original_filename || asset.asset_name}</strong> with external partners or clients.
              </p>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.5rem', fontWeight: '500' }}>
                  <Clock size={14} /> Expiration (Days)
                </label>
                <select 
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(e.target.value === "" ? "" : Number(e.target.value))}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-default)' }}
                >
                  <option value={1}>1 Day</option>
                  <option value={7}>7 Days</option>
                  <option value={30}>30 Days</option>
                  <option value="">Never Expire</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.5rem', fontWeight: '500' }}>
                  <Shield size={14} /> Password Protection (Optional)
                </label>
                <input 
                  type="text" 
                  placeholder="Enter a password or leave blank"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-default)' }}
                />
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Leave blank if you want anyone with the link to view it.
                </p>
              </div>

              {error && (
                <div style={{ padding: '0.75rem', background: 'var(--danger-light, #fef2f2)', color: 'var(--danger, #b91c1c)', borderRadius: '4px', fontSize: '0.85rem', marginBottom: '1rem' }}>
                  {error}
                </div>
              )}

              <button 
                onClick={handleGenerate}
                disabled={loading}
                style={{ width: '100%', padding: '0.75rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '4px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
              >
                {loading ? "Generating..." : "Generate Link"}
              </button>
            </>
          ) : (
            <>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <div style={{ display: 'inline-flex', background: 'var(--success-light, #ecfdf5)', color: 'var(--success, #10b981)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem' }}>
                  <CheckCircle size={32} />
                </div>
                <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Link Generated Successfully</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Anyone with this link {password ? "and the password " : ""}can access this asset.
                </p>
              </div>
              
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                <input 
                  type="text" 
                  readOnly 
                  value={generatedLink}
                  style={{ flex: 1, padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-default)', color: 'var(--text-primary)' }}
                />
                <button 
                  onClick={handleCopy}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0 1rem', background: copied ? 'var(--success, #10b981)' : 'var(--bg-active)', color: copied ? 'white' : 'var(--text-primary)', border: '1px solid', borderColor: copied ? 'var(--success, #10b981)' : 'var(--border)', borderRadius: '4px', fontWeight: '500', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              
              <button 
                onClick={onClose}
                style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-default)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '4px', fontWeight: '500', cursor: 'pointer' }}
              >
                Close
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
