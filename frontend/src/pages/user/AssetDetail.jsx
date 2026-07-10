import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Download, Image, Video, FileText, Folder,
  CheckCircle2, XCircle, Clock3, Globe, Lock, AlertTriangle,
  Tag, Brain, BarChart2, GitBranch, Copy, ExternalLink, CalendarClock, AlertCircle, Link
} from "lucide-react";
import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/layout";
import ShareModal from "../../components/common/ShareModal";
import "../../styles/assetdetail.css";

const TYPE_ICON = {
  "image/jpeg": Image, "image/png": Image,
  "video/mp4": Video, "application/pdf": FileText,
};

const STATUS_CONFIG = {
  approved:       { label: "Approved",    cls: "badge-success",    Icon: CheckCircle2 },
  published:      { label: "Published",   cls: "badge-published",  Icon: Globe },
  draft:          { label: "Draft",       cls: "badge-warning",    Icon: Clock3 },
  pending_review: { label: "In Review",   cls: "badge-info",       Icon: Clock3 },
  rejected:       { label: "Rejected",    cls: "badge-danger",     Icon: XCircle },
  restricted:     { label: "Restricted",  cls: "badge-restricted", Icon: Lock },
};

const computeCompleteness = (asset) => {
  const meta = asset?.asset_metadata || {};
  const mandatory = meta.mandatory || {};
  const business = meta.business || {};
  const checks = [
    !!mandatory.asset_name,
    !!mandatory.description,
    !!mandatory.owner,
    !!mandatory.usage_rights,
    !!business.domain,
    !!business.audience,
    !!business.use_case,
    !!(meta.ai_enrichment?.ai_tags?.length > 0),
  ];
  const score = Math.round((checks.filter(Boolean).length / checks.length) * 100);
  return score;
};

const AssetDetail = () => {
  const { assetId } = useParams();
  const navigate = useNavigate();
  const [asset, setAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [versions, setVersions] = useState([]);
  const [similarAssets, setSimilarAssets] = useState([]);
  const [placements, setPlacements] = useState([]);
  const [newPlacement, setNewPlacement] = useState({ platform: "", placement_url_or_id: "" });
  const [downloadMenuOpen, setDownloadMenuOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);

  useEffect(() => {
    const fetchAssetAndExtras = async () => {
      setLoading(true);
      try {
        const assetRes = await api.get(`/assets/${assetId}`);
        setAsset(assetRes.data);

        // Fetch version history
        try {
          const versionsRes = await api.get(`/assets/${assetId}/versions`);
          setVersions(versionsRes.data.versions || []);
        } catch (err) {
          console.error("Failed to fetch versions:", err);
          setVersions([]);
        }
        // Fetch similar assets (images only)
        if (assetRes.data.asset_type === "image") {
          try {
            const similarRes = await api.get(`/assets/${assetId}/similar?threshold=10`);
            setSimilarAssets(similarRes.data.results || []);
          } catch (err) {
            // 400 = asset has no perceptual hash, which is expected for some images
            if (err.response?.status !== 400) {
              console.error("Failed to fetch similar assets:", err);
            }
            setSimilarAssets([]);
          }
        } else {
          setSimilarAssets([]);
        }

        // Fetch placements
        try {
          const placementsRes = await api.get(`/assets/${assetId}/placements`);
          setPlacements(placementsRes.data || []);
        } catch (err) {
          console.error("Failed to fetch placements:", err);
          setPlacements([]);
        }

      } catch (err) {
        console.error(err);
        navigate("/browse");
      } finally {
        setLoading(false);
      }
    };
    fetchAssetAndExtras();
  }, [assetId, navigate]);

  const executeDownload = async (format = null, width = null, quality = null) => {
    try {
      let query = [];
      if (format) query.push(`format=${format}`);
      if (width) query.push(`width=${width}`);
      if (quality) query.push(`quality=${quality}`);
      const queryStr = query.length > 0 ? `?${query.join("&")}` : "";

      const res = await api.get(`/assets/${assetId}/download${queryStr}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      
      let filename = asset.original_filename;
      if (format) {
         const parts = filename.split(".");
         parts.pop();
         filename = `${parts.join(".")}.${format}`;
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch { alert("Download failed."); }
    setDownloadMenuOpen(false);
  };

  const handleAddPlacement = async (e) => {
    e.preventDefault();
    if (!newPlacement.platform || !newPlacement.placement_url_or_id) return;
    try {
      const res = await api.post(`/assets/${assetId}/placements`, newPlacement);
      setPlacements((prev) => [...prev, res.data]);
      setNewPlacement({ platform: "", placement_url_or_id: "" });
    } catch { alert("Failed to add placement"); }
  };

  const copyId = async () => {
    await navigator.clipboard.writeText(assetId);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (loading) return (
    <Layout>
      <div className="flex-center" style={{ padding: "6rem" }}><div className="loader" /></div>
    </Layout>
  );

  if (!asset) return null;

  const assetName = asset.asset_metadata?.mandatory?.asset_name || asset.original_filename;
  const mandatory = asset.asset_metadata?.mandatory || {};
  const business = asset.asset_metadata?.business || {};
  const content = asset.asset_metadata?.content || {};
  const ai = asset.asset_metadata?.ai_enrichment || {};
  const governance = asset.asset_metadata?.governance || {};

  const statusCfg = STATUS_CONFIG[asset.status] || { label: asset.status, cls: "badge-warning", Icon: Clock3 };
  const StatusIcon = statusCfg.Icon;
  const FileIcon = TYPE_ICON[asset.mime_type] || Folder;

  const token = localStorage.getItem("access_token");
  const rawPreview = asset.thumbnail_url || asset.preview_url || asset.thumbnail_path || asset.preview_path || asset.storage_path;
  const previewUrl = rawPreview?.startsWith("http") ? rawPreview : `${API_BASE}/assets/${asset.id}/preview${token ? `?token=${token}` : ''}`;

  const completeness = computeCompleteness(asset);
  const completenessColor = completeness >= 80 ? "var(--success)" : completeness >= 50 ? "var(--warning)" : "var(--danger)";

  const tags = ai.ai_tags || [];
  const detectedObjects = ai.detected_objects || [];
  const keywords = content.keywords || [];

  return (
    <Layout>
      <div className="asset-detail-page">
        {/* BACK + ACTIONS */}
        <div className="asset-detail-topbar">
          <button className="asset-detail-back" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} />
            Back
          </button>
          <div className="asset-detail-actions">
            <div style={{ position: "relative" }}>
              <button 
                className="btn-premium" 
                onClick={() => setDownloadMenuOpen(!downloadMenuOpen)}
                style={{ display: "flex", gap: "8px", alignItems: "center" }}
              >
                <Download size={16} />
                Download Options
              </button>
              {downloadMenuOpen && (
                <div style={{ position: "absolute", top: "100%", right: 0, marginTop: "4px", background: "white", border: "1px solid #e2e8f0", borderRadius: "6px", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)", zIndex: 50, minWidth: "200px" }}>
                  <button style={{ width: "100%", textAlign: "left", padding: "10px 14px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.85rem", borderBottom: "1px solid #f1f5f9" }} onClick={() => executeDownload()}>
                    Original File
                  </button>
                  {asset.renditions && asset.renditions.length > 0 && asset.renditions.map(rend => (
                    <button 
                      key={rend.id} 
                      style={{ width: "100%", textAlign: "left", padding: "10px 14px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.85rem", borderBottom: "1px solid #f1f5f9" }} 
                      onClick={() => {
                        // Assuming Cloudinary handles direct download or we open it
                        window.open(rend.storage_path, '_blank');
                        setDownloadMenuOpen(false);
                      }}
                    >
                      Rendition: {rend.rendition_name} {rend.width && rend.height ? `(${rend.width}x${rend.height})` : ""}
                    </button>
                  ))}
                  {(!asset.renditions || asset.renditions.length === 0) && (
                    <>
                      <button style={{ width: "100%", textAlign: "left", padding: "10px 14px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.85rem", borderBottom: "1px solid #f1f5f9" }} onClick={() => executeDownload("webp", 1080, "auto")}>
                        Web-Ready (Auto-Gen)
                      </button>
                      <button style={{ width: "100%", textAlign: "left", padding: "10px 14px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.85rem" }} onClick={() => executeDownload(null, 400, "auto")}>
                        Thumbnail (Auto-Gen)
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
            {previewUrl && (
              <a href={previewUrl} target="_blank" rel="noreferrer" className="asset-detail-btn-secondary">
                <ExternalLink size={16} />
                Open Original
              </a>
            )}
            <button 
              className="btn-premium" 
              onClick={() => setShareModalOpen(true)}
              style={{ display: "flex", gap: "8px", alignItems: "center" }}
            >
              <Link size={16} />
              Share
            </button>
          </div>
        </div>

        <div className="asset-detail-layout">
          {/* LEFT COLUMN — PREVIEW */}
          <div className="asset-detail-left">
            <div className="asset-detail-preview">
              {asset.mime_type?.startsWith("image/") && previewUrl ? (
                <img src={previewUrl} alt={assetName} />
              ) : asset.mime_type === "application/pdf" && previewUrl ? (
                <iframe src={previewUrl} title={assetName} />
              ) : asset.mime_type?.startsWith("video/") && previewUrl ? (
                <video src={previewUrl} controls />
              ) : (
                <div className="asset-detail-preview-placeholder">
                  <FileIcon size={64} />
                  <p>No preview available</p>
                </div>
              )}
            </div>

            {/* COMPLETENESS SCORE */}
            <div className="asset-detail-card completeness-card">
              <div className="card-header">
                <BarChart2 size={15} />
                <span>Metadata Completeness</span>
              </div>
              <div className="completeness-track">
                <div
                  className="completeness-fill"
                  style={{ width: `${completeness}%`, background: completenessColor }}
                />
              </div>
              <div className="completeness-label" style={{ color: completenessColor }}>
                {completeness}% Complete
              </div>
              {completeness < 80 && (
                <div className="completeness-warning">
                  <AlertTriangle size={13} />
                  Some metadata fields are missing
                </div>
              )}
            </div>

            {/* AI ENRICHMENT */}
            {(tags.length > 0 || ai.image_caption || detectedObjects.length > 0) && (
              <div className="asset-detail-card">
                <div className="card-header">
                  <Brain size={15} />
                  <span>AI Enrichment</span>
                  {ai.enrichment_status === "completed" && (
                    <span className="badge badge-accent" style={{ marginLeft: "auto", fontSize: "0.65rem" }}>AI Tagged</span>
                  )}
                </div>
                {ai.image_caption && (
                  <div className="ai-caption">
                    <span className="detail-label">Caption</span>
                    <p>{ai.image_caption}</p>
                  </div>
                )}
                {tags.length > 0 && (
                  <div className="ai-tags-section">
                    <span className="detail-label">AI Tags</span>
                    <div className="detail-tags">
                      {tags.map((t) => <span key={t} className="asset-tag">{t}</span>)}
                    </div>
                  </div>
                )}
                {detectedObjects.length > 0 && (
                  <div className="ai-tags-section">
                    <span className="detail-label">Detected Objects</span>
                    <div className="detail-tags">
                      {detectedObjects.map((o) => <span key={o} className="asset-tag">{o}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN — METADATA */}
          <div className="asset-detail-right">
            {/* TITLE ROW */}
            <div className="asset-detail-title-row">
              <h1 className="asset-detail-name">{assetName}</h1>
              <div className="asset-detail-chips">
                <span className={`badge ${statusCfg.cls}`}>
                  <StatusIcon size={11} />
                  {statusCfg.label}
                </span>
                {asset.is_latest ? (
                  <span className="badge badge-success">Latest</span>
                ) : (
                  <span className="badge badge-danger">Outdated</span>
                )}
                {asset.version > 1 && (
                  <span className="badge badge-accent">v{asset.version}</span>
                )}
              </div>
            </div>

            {mandatory.description && (
              <p className="asset-detail-description">{mandatory.description}</p>
            )}

            {/* EXPIRY BANNER */}
            {asset.expired && (
              <div className="expiry-banner expiry-banner--expired">
                <AlertCircle size={16} />
                <div className="expiry-banner-text">
                  <strong>Asset Expired</strong>
                  <span>
                    This asset expired on{" "}
                    <strong>{business.expiry_date}</strong> and has been automatically restricted.
                  </span>
                </div>
              </div>
            )}
            {!asset.expired && asset.expiring_soon && (
              <div className="expiry-banner expiry-banner--soon">
                <CalendarClock size={16} />
                <div className="expiry-banner-text">
                  <strong>Expiring Soon</strong>
                  <span>
                    This asset expires on{" "}
                    <strong>{business.expiry_date}</strong>
                    {asset.days_until_expiry != null && (
                      <> — <strong>{asset.days_until_expiry} day{asset.days_until_expiry === 1 ? "" : "s"} remaining</strong></>
                    )}
                  </span>
                </div>
              </div>
            )}

            {/* MANDATORY METADATA */}
            <div className="asset-detail-card">
              <div className="card-header"><FileIcon size={15} /><span>Core Metadata</span></div>
              <div className="detail-grid">
                <DetailRow label="Asset Type" value={mandatory.asset_type} />
                <DetailRow label="Owner" value={mandatory.owner} />
                <DetailRow label="Created By" value={mandatory.created_by} />
                <DetailRow label="Usage Rights" value={mandatory.usage_rights} />
                <DetailRow label="File Size" value={asset.file_size ? `${(asset.file_size / 1024).toFixed(1)} KB` : null} />
                <DetailRow label="Format" value={asset.mime_type} />
                <DetailRow label="Uploaded" value={asset.created_at ? new Date(asset.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" }) : null} />
              </div>
            </div>

            {/* BUSINESS METADATA */}
            <div className="asset-detail-card">
              <div className="card-header"><Globe size={15} /><span>Business Context</span></div>
              <div className="detail-grid">
                <DetailRow label="Domain" value={business.domain} />
                <DetailRow label="Audience" value={business.audience} />
                <DetailRow label="Use Case" value={business.use_case} />
                <DetailRow label="Funnel Stage" value={business.funnel_stage} />
              </div>
            </div>

            {/* CONTENT METADATA */}
            {(content.tone || keywords.length > 0) && (
              <div className="asset-detail-card">
                <div className="card-header"><Tag size={15} /><span>Content Details</span></div>
                <DetailRow label="Tone" value={content.tone} />
                {keywords.length > 0 && (
                  <div style={{ marginTop: "0.75rem" }}>
                    <span className="detail-label">Keywords</span>
                    <div className="detail-tags" style={{ marginTop: "0.4rem" }}>
                      {keywords.map((k) => <span key={k} className="asset-tag">{k}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* GOVERNANCE */}
            {(asset.website_safe || asset.public_use_approved || governance.restriction_reason || governance.publish_note || governance.published_channels?.length > 0 || asset.geographic_restrictions || asset.platform_restrictions || asset.source_ownership || asset.model_release_status !== "Not Required") && (
              <div className="asset-detail-card">
                <div className="card-header"><Lock size={15} /><span>Governance</span></div>
                <DetailRow label="Website Safe" value={asset.website_safe ? "Yes" : "No"} />
                <DetailRow label="Public Use" value={asset.public_use_approved ? "Yes" : "No"} />
                <DetailRow label="Source Ownership" value={asset.source_ownership} />
                <DetailRow label="Model Release" value={asset.model_release_status} />
                
                {asset.geographic_restrictions?.length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <span className="detail-label">Geographic Restrictions</span>
                    <div className="detail-tags" style={{ marginTop: "0.4rem" }}>
                      {asset.geographic_restrictions.map((c) => <span key={c} className="asset-tag">{c}</span>)}
                    </div>
                  </div>
                )}
                
                {asset.platform_restrictions?.length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <span className="detail-label">Platform Restrictions</span>
                    <div className="detail-tags" style={{ marginTop: "0.4rem" }}>
                      {asset.platform_restrictions.map((p) => <span key={p} className="asset-tag">{p}</span>)}
                    </div>
                  </div>
                )}

                <DetailRow label="Restriction Reason" value={governance.restriction_reason} />
                <DetailRow label="Publish Note" value={governance.publish_note} />
                {governance.published_channels?.length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <span className="detail-label">Published Channels</span>
                    <div className="detail-tags" style={{ marginTop: "0.4rem" }}>
                      {governance.published_channels.map((c) => <span key={c} className="asset-tag">{c}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* LIVE PLACEMENTS */}
            <div className="asset-detail-card">
              <div className="card-header"><Globe size={15} /><span>Live Placements</span></div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                {placements.map((p) => (
                  <div key={p.id} style={{ fontSize: "0.85rem", display: "flex", justifyContent: "space-between", padding: "8px", background: "#f8fafc", borderRadius: "6px" }}>
                    <strong>{p.platform}</strong>
                    <a href={p.placement_url_or_id.startsWith("http") ? p.placement_url_or_id : `http://${p.placement_url_or_id}`} target="_blank" rel="noreferrer" style={{ color: "var(--accent)" }}>
                      Link
                    </a>
                  </div>
                ))}
                {placements.length === 0 && <span style={{ fontSize: "0.85rem", color: "#64748b" }}>No placements tracked yet.</span>}
                <form onSubmit={handleAddPlacement} style={{ display: "flex", gap: "6px", marginTop: "10px" }}>
                  <input type="text" placeholder="Platform (e.g. HubSpot)" value={newPlacement.platform} onChange={e => setNewPlacement({ ...newPlacement, platform: e.target.value })} style={{ flex: 1, padding: "6px 10px", fontSize: "0.8rem", border: "1px solid #e2e8f0", borderRadius: "4px" }} />
                  <input type="text" placeholder="URL" value={newPlacement.placement_url_or_id} onChange={e => setNewPlacement({ ...newPlacement, placement_url_or_id: e.target.value })} style={{ flex: 1, padding: "6px 10px", fontSize: "0.8rem", border: "1px solid #e2e8f0", borderRadius: "4px" }} />
                  <button type="submit" style={{ padding: "6px 10px", fontSize: "0.8rem", background: "var(--accent)", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}>Add</button>
                </form>
              </div>
            </div>

            {/* ASSET RELATIONSHIPS (Master / Derivatives) */}
            {(asset.master_asset || (asset.derivatives && asset.derivatives.length > 0)) && (
              <div className="asset-detail-card">
                <div className="card-header"><GitBranch size={15} /><span>Asset Relationships</span></div>
                
                {asset.master_asset && (
                  <div style={{ marginTop: "10px" }}>
                    <span className="detail-label">Master Asset</span>
                    <div 
                      className="version-item" 
                      onClick={() => navigate(`/assets/${asset.master_asset.id}`)}
                      style={{ marginTop: "5px", cursor: "pointer", border: "1px solid var(--border)", padding: "8px", borderRadius: "6px" }}
                    >
                      <strong>{asset.master_asset.original_filename}</strong>
                    </div>
                  </div>
                )}

                {asset.derivatives && asset.derivatives.length > 0 && (
                  <div style={{ marginTop: "10px" }}>
                    <span className="detail-label">Derivatives ({asset.derivatives.length})</span>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "5px" }}>
                      {asset.derivatives.map(d => (
                        <div 
                          key={d.id} 
                          className="version-item"
                          onClick={() => navigate(`/assets/${d.id}`)}
                          style={{ cursor: "pointer", border: "1px solid var(--border)", padding: "8px", borderRadius: "6px" }}
                        >
                          <strong>{d.original_filename}</strong> <span style={{fontSize: "0.8rem", color: "#64748b"}}>v{d.version}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* VERSION HISTORY TREE */}
            <div className="asset-detail-card version-history-card">
              <div className="card-header">
                <GitBranch size={15} />
                <span>Version History</span>
              </div>
              <div className="version-list">
                {versions.map((ver) => {
                  const isCurrent = ver.id === assetId;
                  const dateStr = ver.created_at ? new Date(ver.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" }) : "";
                  return (
                    <div
                      key={ver.id}
                      className={`version-item ${isCurrent ? "version-item--current" : ""}`}
                      onClick={() => !isCurrent && navigate(`/assets/${ver.id}`)}
                    >
                      <div className="version-item-header">
                        <span className="version-num">Version {ver.version}</span>
                        {ver.is_latest && <span className="badge badge-success">Latest</span>}
                        {isCurrent && <span className="current-indicator">Viewing</span>}
                      </div>
                      {ver.changelog && <p className="version-changelog">“{ver.changelog}”</p>}
                      <div className="version-meta">
                        <span className="version-author">By {ver.updated_by || "System"}</span>
                        <span className="version-date">{dateStr}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="asset-id-row" style={{ marginTop: "0.5rem" }}>
                <span className="detail-label">Asset ID</span>
                <div className="asset-id-copy">
                  <code>{asset.id}</code>
                  <button onClick={copyId} className="copy-btn">
                    <Copy size={13} />
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* VISUALLY SIMILAR ASSETS */}
        {similarAssets.length > 0 && (
          <div className="similar-assets-section">
            <h3 className="similar-assets-title">Visually Similar Assets</h3>
            <div className="similar-assets-grid">
              {similarAssets.map((sim) => {
                const simName = sim.original_filename;
                const matchPct = Math.round(sim.similarity * 100);
                const rawSimPreview = sim.thumbnail_path || sim.preview_path || sim.storage_path;
                const simPreviewUrl = rawSimPreview?.startsWith("http") ? rawSimPreview : rawSimPreview ? `${API_BASE}/assets/${sim.id}/preview` : null;
                return (
                  <div key={sim.id} className="similar-asset-card" onClick={() => navigate(`/assets/${sim.id}`)}>
                    <div className="similar-thumb">
                      {simPreviewUrl ? (
                        <img src={simPreviewUrl} alt={simName} />
                      ) : (
                        <Folder size={32} />
                      )}
                      <div className="similarity-badge">{matchPct}% match</div>
                    </div>
                    <div className="similar-info">
                      <div className="similar-name" title={simName}>{simName}</div>
                      <div className="similar-meta">
                        <span className="badge badge-accent">v{sim.version}</span>
                        <span className={`badge ${sim.status === 'approved' || sim.status === 'published' ? 'badge-success' : 'badge-warning'}`}>{sim.status}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      {shareModalOpen && (
        <ShareModal 
          asset={asset}
          onClose={() => setShareModalOpen(false)}
        />
      )}
    </Layout>
  );
};

const DetailRow = ({ label, value, mono }) => {
  if (!value) return null;
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className={`detail-value ${mono ? "detail-mono" : ""}`}>{value}</span>
    </div>
  );
};

export default AssetDetail;
