import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Download, Image, Video, FileText, Folder,
  CheckCircle2, XCircle, Clock3, Globe, Lock, AlertTriangle,
  Tag, Brain, BarChart2, GitBranch, Copy, ExternalLink
} from "lucide-react";
import api, { API_BASE } from "../../api/axios";
import Layout from "../../components/common/layout";
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

        // Fetch similar assets if it's an image
        if (assetRes.data.mime_type?.startsWith("image/")) {
          try {
            const similarRes = await api.get(`/assets/${assetId}/similar`);
            setSimilarAssets(similarRes.data || []);
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

      } catch (err) {
        console.error(err);
        navigate("/browse");
      } finally {
        setLoading(false);
      }
    };
    fetchAssetAndExtras();
  }, [assetId, navigate]);

  const handleDownload = async () => {
    try {
      const res = await api.get(`/assets/${assetId}/download`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = asset.original_filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch { alert("Download failed."); }
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

  const rawPreview = asset.thumbnail_url || asset.preview_url || asset.thumbnail_path || asset.preview_path || asset.storage_path;
  const previewUrl = rawPreview?.startsWith("http") ? rawPreview : `${API_BASE}/assets/${asset.id}/preview`;

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
            <button className="asset-detail-btn-primary" onClick={handleDownload}>
              <Download size={16} />
              Download
            </button>
            {previewUrl && (
              <a href={previewUrl} target="_blank" rel="noreferrer" className="asset-detail-btn-secondary">
                <ExternalLink size={16} />
                Open Original
              </a>
            )}
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
            {(governance.restriction_reason || governance.publish_note || governance.published_channels?.length > 0) && (
              <div className="asset-detail-card">
                <div className="card-header"><Lock size={15} /><span>Governance</span></div>
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
