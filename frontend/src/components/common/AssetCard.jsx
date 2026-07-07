import { Image, Video, FileText, Folder, Clock, AlertCircle, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

import "../../styles/assetcard.css";
import { API_BASE } from "../../api/axios";

const TYPE_ICON = {
  "image/jpeg": <Image size={18} className="asset-file-icon image" />,

  "image/png": <Image size={18} className="asset-file-icon image" />,

  "video/mp4": <Video size={18} className="asset-file-icon video" />,

  "application/pdf": <FileText size={18} className="asset-file-icon pdf" />,
};

const STATUS_CONFIG = {
  approved:       { label: "Approved",    cls: "badge-success" },
  published:      { label: "Published",   cls: "badge-published" },
  draft:          { label: "Draft",       cls: "badge-warning" },
  pending_review: { label: "In Review",   cls: "badge-info" },
  rejected:       { label: "Rejected",    cls: "badge-danger" },
  restricted:     { label: "Restricted",  cls: "badge-restricted" },
  archived:       { label: "Archived",    cls: "badge-muted" },
};

const AssetCard = ({
  asset,
  onClick,
  score,
  semanticScore,
  keywordScore,
  searchMode,
}) => {
  const navigate = useNavigate();
  const [imgError, setImgError] = useState(false);
  const icon = TYPE_ICON[asset.mime_type] || (
    <Folder size={18} className="asset-file-icon default" />
  );

  const assetName =
    asset.asset_metadata?.mandatory?.asset_name || asset.original_filename;

  const tags = Array.isArray(asset.asset_metadata?.ai_enrichment?.ai_tags) 
    ? asset.asset_metadata.ai_enrichment.ai_tags.slice(0, 3) 
    : [];

  const description = asset.asset_metadata?.mandatory?.description || "";

  const domain = asset.asset_metadata?.business?.domain || "";

  const assetType = asset.asset_metadata?.mandatory?.asset_type || "asset";

  const status = asset.status;
  const statusCfg = STATUS_CONFIG[status] || { label: status, cls: "badge-warning" };

  const hasAiEnrichment = !!(asset.asset_metadata?.ai_enrichment?.enrichment_status === "completed");

  // Missing metadata: no description or no domain
  const isMissingMeta =
    !asset.asset_metadata?.mandatory?.description ||
    !asset.asset_metadata?.business?.domain;

  // Expiry flags — computed by backend ExpiryService and returned in asset response
  const isExpired = asset.expired === true;
  const isExpiringSoon = asset.expiring_soon === true;
  const daysUntilExpiry = asset.days_until_expiry ?? null;

  let previewUrl = asset.thumbnail_path?.startsWith("http")
    ? asset.thumbnail_path
    : asset.preview_path?.startsWith("http")
      ? asset.preview_path
      : `${API_BASE}/assets/${asset.id}/preview`;

  // Fix for PDF thumbnails from Cloudinary
  if (asset.mime_type === "application/pdf" && previewUrl.includes("cloudinary.com") && previewUrl.endsWith(".pdf")) {
    previewUrl = previewUrl.replace(/\.pdf$/i, ".jpg");
  }

  const hasPreview = asset.thumbnail_path || asset.preview_path;

  return (
    <div className="asset-card" onClick={onClick}>
      <div className="asset-card-inner">
        {/* FRONT */}

        <div className="asset-card-front">
          <div className="asset-card-thumb">
            {hasPreview && !imgError ? (
              <img 
                src={previewUrl} 
                alt={assetName} 
                loading="lazy" 
                onError={() => setImgError(true)}
              />
            ) : asset.mime_type === "application/pdf" ? (
              <iframe 
                src={previewUrl} 
                title={assetName}
                style={{ width: '100%', height: '100%', border: 'none', pointerEvents: 'none', overflow: 'hidden' }}
                scrolling="no"
              />
            ) : (
              <div className="asset-card-icon">{icon}</div>
            )}

            {typeof score === "number" && (
              <div className="asset-score-badge">
                {Math.round(score * 100)}%
                {searchMode === "hybrid" ? " hybrid" : " match"}
              </div>
            )}

            {/* STATUS BADGE — always visible on front */}
            <div className={`asset-status-badge badge ${statusCfg.cls}`}>
              {statusCfg.label}
            </div>

            {/* EXPIRY BADGES */}
            {isExpired && (
              <div className="asset-expiry-badge asset-expiry-badge--expired" title="This asset has expired and is restricted">
                <AlertCircle size={11} />
                EXPIRED
              </div>
            )}
            {!isExpired && isExpiringSoon && (
              <div className="asset-expiry-badge asset-expiry-badge--soon" title={`Expires in ${daysUntilExpiry} day${daysUntilExpiry === 1 ? '' : 's'}`}>
                <Clock size={11} />
                {daysUntilExpiry !== null ? `${daysUntilExpiry}d left` : 'EXPIRING SOON'}
              </div>
            )}

            {/* GOVERNANCE BADGES */}
            {(asset.website_safe || asset.public_use_approved) && (
              <div className="asset-governance-badges" style={{ position: "absolute", top: "8px", left: "8px", display: "flex", gap: "4px" }}>
                {asset.website_safe && (
                  <div className="badge" style={{ backgroundColor: "#10b981", color: "white", padding: "2px 6px", fontSize: "10px", borderRadius: "12px", display: "flex", alignItems: "center", gap: "2px" }} title="Website Safe">
                    <ShieldCheck size={10} /> Web
                  </div>
                )}
                {asset.public_use_approved && (
                  <div className="badge" style={{ backgroundColor: "#10b981", color: "white", padding: "2px 6px", fontSize: "10px", borderRadius: "12px", display: "flex", alignItems: "center", gap: "2px" }} title="Public Use Approved">
                    <ShieldCheck size={10} /> Public
                  </div>
                )}
              </div>
            )}

            {/* MISSING METADATA WARNING */}
            {isMissingMeta && (
              <div className="asset-missing-meta" title="Missing metadata">
                ⚠
              </div>
            )}
          </div>

          <div className="asset-card-front-info">
            <span className="asset-card-name">{assetName}</span>

            <div className="asset-card-meta-row">
              <span className="asset-card-type">
                {icon}
                {assetType}
              </span>

              {asset.version > 1 && (
                <span className="asset-version-chip">v{asset.version}</span>
              )}

              {hasAiEnrichment && (
                <span className="asset-ai-chip">AI</span>
              )}

              {!asset.is_latest && (
                <span className="asset-outdated-chip">Outdated</span>
              )}
            </div>
          </div>
        </div>

        {/* BACK */}

        <div className="asset-card-back">
          <div className="asset-card-back-content">
            <p className="asset-card-desc">
              {description || "No description available."}
            </p>

            <div className="asset-card-meta">
              {domain && <span className="badge badge-accent">{domain}</span>}

              <span
                className={`badge ${
                  status === "approved"
                    ? "badge-success"
                    : status === "rejected"
                      ? "badge-danger"
                      : "badge-warning"
                }`}
              >
                {status}
              </span>
            </div>

            {searchMode === "hybrid" &&
              typeof semanticScore === "number" &&
              typeof keywordScore === "number" && (
                <div className="asset-scores">
                  <div className="asset-score-row">
                    <span>Semantic</span>

                    <span>{Math.round(semanticScore * 100)}%</span>
                  </div>

                  <div className="asset-score-row">
                    <span>Keyword</span>

                    <span>{Math.round(keywordScore * 100)}%</span>
                  </div>
                </div>
              )}

            {tags.length > 0 && (
              <div className="asset-card-tags">
                {tags.map((tag) => (
                  <span key={tag} className="asset-tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <button
              className="asset-card-btn"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/assets/${asset.id}`);
              }}
            >
              View Details →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetCard;
