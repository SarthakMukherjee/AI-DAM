import "../../styles/assetcard.css";

const TYPE_ICON = {
  "image/jpeg": "🖼️",
  "image/png": "🖼️",
  "video/mp4": "🎬",
  "application/pdf": "📄",
};

const AssetCard = ({ asset, onClick, score }) => {
  const icon = TYPE_ICON[asset.mime_type] || "📁";

  const assetName =
    asset.asset_metadata?.mandatory?.asset_name ||
    asset.original_filename;

  const tags =
    asset.asset_metadata?.ai_enrichment?.ai_tags?.slice(0, 3) || [];

  const description =
    asset.asset_metadata?.mandatory?.description || "";

  const domain =
    asset.asset_metadata?.business?.domain || "";

  const assetType =
    asset.asset_metadata?.mandatory?.asset_type || "";

  const status = asset.status;

  return (
    <div className="asset-card" onClick={onClick}>
      <div className="asset-card-inner">

        {/* FRONT */}
        <div className="asset-card-front">
          <div className="asset-card-thumb">
            {asset.thumbnail_path || asset.preview_path ? (
              <img
                src={`http://localhost:8000/assets/${asset.id}/preview`}
                alt={assetName}
                loading="lazy"
              />
            ) : (
              <div className="asset-card-icon">{icon}</div>
            )}
          </div>

          {/* SCORE BADGE — shown in search mode */}
          {score !== undefined && (
            <div className="asset-score-badge">
              {Math.round(score * 100)}% match
            </div>
          )}

          <div className="asset-card-front-info">
            <span className="asset-card-name">{assetName}</span>
            <span className="asset-card-type">{icon} {assetType}</span>
          </div>
        </div>

        {/* BACK */}
        <div className="asset-card-back">
          <div className="asset-card-back-content">

            <p className="asset-card-desc">
              {description || "No description available."}
            </p>

            <div className="asset-card-meta">
              {domain && (
                <span className="badge badge-accent">{domain}</span>
              )}
              <span className={`badge ${
                status === "approved" ? "badge-success"
                : status === "rejected" ? "badge-danger"
                : "badge-warning"
              }`}>
                {status}
              </span>
            </div>

            {tags.length > 0 && (
              <div className="asset-card-tags">
                {tags.map((tag) => (
                  <span key={tag} className="asset-tag">{tag}</span>
                ))}
              </div>
            )}

            <button className="asset-card-btn">
              View Details →
            </button>

          </div>
        </div>

      </div>
    </div>
  );
};

export default AssetCard;