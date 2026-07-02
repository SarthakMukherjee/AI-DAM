import { Image, Video, FileText, Folder } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
  const icon = TYPE_ICON[asset.mime_type] || (
    <Folder size={18} className="asset-file-icon default" />
  );

  const assetName =
    asset.asset_metadata?.mandatory?.asset_name || asset.original_filename;

  const tags = asset.asset_metadata?.ai_enrichment?.ai_tags?.slice(0, 3) || [];

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

  const previewUrl = asset.thumbnail_path?.startsWith("http")
    ? asset.thumbnail_path
    : asset.preview_path?.startsWith("http")
      ? asset.preview_path
      : `${API_BASE}/assets/${asset.id}/preview`;

  const hasPreview = asset.thumbnail_path || asset.preview_path;

  return (
    <div className="asset-card" onClick={onClick}>
      <div className="asset-card-inner">
        {/* FRONT */}

        <div className="asset-card-front">
          <div className="asset-card-thumb">
            {hasPreview ? (
              <img src={previewUrl} alt={assetName} loading="lazy" />
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
