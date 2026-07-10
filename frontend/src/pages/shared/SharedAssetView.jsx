import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Lock, FileText, Download, CheckCircle, AlertCircle } from "lucide-react";
import api, { API_BASE } from "../../api/axios";

// Minimal public layout just for shared links
const SharedAssetView = () => {
  const { token } = useParams();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [linkInfo, setLinkInfo] = useState(null);
  const [password, setPassword] = useState("");
  const [assetData, setAssetData] = useState(null);
  
  useEffect(() => {
    const fetchLinkInfo = async () => {
      try {
        const res = await api.get(`/shared-links/${token}`);
        setLinkInfo(res.data);
        if (!res.data.has_password) {
          // Attempt to access immediately if no password required
          accessAsset("");
        }
      } catch (err) {
        console.error(err);
        setError(err.response?.data?.detail || "Invalid or expired link");
      } finally {
        setLoading(false);
      }
    };
    
    fetchLinkInfo();
  }, [token]);

  const accessAsset = async (pwd) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post(`/shared-links/${token}/access`, { password: pwd });
      setAssetData(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to access asset");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (!password) return;
    accessAsset(password);
  };
  
  const handleDownload = () => {
    if (!assetData) return;
    // Real implementation would use the signed URL from the backend
    // For now, we simulate by opening the storage_path if it's an HTTP URL or the preview API
    const downloadUrl = assetData.storage_path?.startsWith("http") 
      ? assetData.storage_path 
      : `${API_BASE}/assets/${assetData.asset_id}/download`; // Note: This might still require auth in real impl unless we have a specific public download endpoint
    
    window.open(downloadUrl, "_blank");
  };

  if (loading && !linkInfo) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-default)' }}>
        <div className="loader" />
      </div>
    );
  }

  if (error && !assetData) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-default)' }}>
        <div style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '8px', textAlign: 'center', border: '1px solid var(--border)', maxWidth: '400px' }}>
          <AlertCircle size={48} style={{ color: 'var(--danger)', margin: '0 auto 1rem' }} />
          <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Access Denied</h2>
          <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      </div>
    );
  }
  
  if (linkInfo?.has_password && !assetData) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-default)' }}>
        <div style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '8px', border: '1px solid var(--border)', width: '100%', maxWidth: '400px', boxShadow: 'var(--shadow-md)' }}>
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <div style={{ background: 'var(--bg-active)', width: '60px', height: '60px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
              <Lock size={28} style={{ color: 'var(--primary)' }} />
            </div>
            <h2 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Password Protected</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>This shared asset requires a password to view.</p>
          </div>
          
          <form onSubmit={handlePasswordSubmit}>
            <div style={{ marginBottom: '1rem' }}>
              <input 
                type="password" 
                placeholder="Enter password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                style={{ width: '100%', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-default)' }}
              />
            </div>
            {error && (
              <div style={{ color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '1rem', textAlign: 'center' }}>
                {error}
              </div>
            )}
            <button 
              type="submit" 
              disabled={loading || !password}
              style={{ width: '100%', padding: '0.75rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '4px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}
            >
              {loading ? "Verifying..." : "Access Asset"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (assetData) {
    let previewUrl = assetData.preview_path?.startsWith("http")
      ? assetData.preview_path
      : assetData.thumbnail_path?.startsWith("http")
        ? assetData.thumbnail_path
        : `${API_BASE}/assets/${assetData.asset_id}/preview`; // Also might need auth bypass for shared

    if (assetData.mime_type === "application/pdf" && previewUrl.includes("cloudinary.com") && previewUrl.endsWith(".pdf")) {
      previewUrl = previewUrl.replace(/\.pdf$/i, ".jpg");
    }
    
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-default)', display: 'flex', flexDirection: 'column' }}>
        <header style={{ padding: '1rem 2rem', background: 'var(--surface)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '1.25rem' }}>AI-DAM Shared Asset</div>
          <button 
            onClick={handleDownload}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '4px', fontWeight: '500', cursor: 'pointer' }}
          >
            <Download size={16} />
            Download Original
          </button>
        </header>
        
        <main style={{ flex: 1, padding: '2rem', display: 'flex', justifyContent: 'center' }}>
          <div style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '8px', border: '1px solid var(--border)', width: '100%', maxWidth: '900px', boxShadow: 'var(--shadow-sm)' }}>
            <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              {assetData.original_filename}
            </h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              {assetData.mime_type} • Shared via secure link
            </p>
            
            <div style={{ background: 'var(--bg-active)', borderRadius: '8px', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
              {assetData.mime_type?.startsWith("image/") ? (
                <img src={previewUrl} alt={assetData.original_filename} style={{ maxWidth: '100%', maxHeight: '600px', objectFit: 'contain' }} />
              ) : assetData.mime_type?.startsWith("video/") ? (
                <video src={previewUrl} controls style={{ maxWidth: '100%', maxHeight: '600px' }} />
              ) : assetData.mime_type === "application/pdf" ? (
                <iframe src={previewUrl} title={assetData.original_filename} style={{ width: '100%', height: '600px', border: 'none' }} />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: 'var(--text-secondary)' }}>
                  <FileText size={64} style={{ marginBottom: '1rem' }} />
                  <span>Preview not available for this file type</span>
                </div>
              )}
            </div>
            
            {assetData.asset_metadata?.mandatory?.description && (
              <div style={{ marginTop: '2rem' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Description</h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {assetData.asset_metadata.mandatory.description}
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }
  
  return null;
};

export default SharedAssetView;
