import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import {
  Image,
  Video,
  FileText,
  Folder,
  Download,
  Trash2,
  X,
  Copy,
  GitBranch,
  Eye,
  Archive,
} from "lucide-react";

import api from "../../api/axios";

import "../../styles/assetmodal.css";

const TYPE_ICON = {
  "image/jpeg": <Image size={22} className="modal-file-icon image" />,
  "image/png": <Image size={22} className="modal-file-icon image" />,
  "video/mp4": <Video size={22} className="modal-file-icon video" />,
  "application/pdf": <FileText size={22} className="modal-file-icon pdf" />,
};

const AssetModal = ({ asset, onClose, onDelete, onArchive, showDelete }) => {
  const navigate = useNavigate();
  const assetName =
    asset.asset_metadata?.mandatory?.asset_name || asset.original_filename;

  const description = asset.asset_metadata?.mandatory?.description || "—";

  const tags = asset.asset_metadata?.ai_enrichment?.ai_tags || [];

  const caption = asset.asset_metadata?.ai_enrichment?.image_caption || "";

  const mandatory = asset.asset_metadata?.mandatory || {};

  const business = asset.asset_metadata?.business || {};

  const content = asset.asset_metadata?.content || {};

  const icon = TYPE_ICON[asset.mime_type] || (
    <Folder size={22} className="modal-file-icon default" />
  );

  // Cloudinary-aware preview URL
  const previewUrl =
    asset.thumbnail_url ||
    asset.preview_url ||
    asset.thumbnail_path ||
    asset.preview_path ||
    asset.storage_path;

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handler);

    return () => {
      document.removeEventListener("keydown", handler);
    };
  }, [onClose]);

  useEffect(() => {
    console.log("AssetModal asset:", asset);
    console.log("Preview URL:", previewUrl);
  }, [asset, previewUrl]);

  const copyAssetId = async () => {
    try {
      await navigator.clipboard.writeText(asset.id);
      alert("Asset ID copied!");
    } catch {
      alert("Failed to copy asset ID");
    }
  };

  const handleDownload = async () => {
    try {
      const res = await api.get(`/assets/${asset.id}/download`, {
        responseType: "blob",
      });

      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = asset.original_filename;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Download failed. Please try again.");
    }
  };

  const handleArchive = async () => {
    const reason = window.prompt("Archive reason (optional):") ?? "";
    if (reason === null) return;
    try {
      const formData = new FormData();
      if (reason) formData.append("reason", reason);
      await api.patch(`/assets/${asset.id}/archive`, formData);
      alert("Asset archived successfully.");
      onClose();
      if (onArchive) onArchive(asset.id);
    } catch (err) {
      alert(err?.response?.data?.detail || "Archive failed. Please try again.");
    }
  };

  const statusBadge =
    asset.status === "approved"
      ? "badge-success"
      : asset.status === "rejected"
        ? "badge-danger"
        : "badge-warning";

  const versionChip = asset.is_latest
    ? "version-chip-latest"
    : "version-chip-old";

  const versionLabel = asset.is_latest ? "Latest Version" : "Outdated Version";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* HEADER */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">{icon}</span>

            <div>
              <h2 className="modal-title">{assetName}</h2>

              <span className="modal-filename">{asset.original_filename}</span>
            </div>
          </div>

          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* LEFT — PREVIEW */}
          <div className="modal-preview">
            {asset.mime_type?.startsWith("image/") ? (
              <img
                src={previewUrl}
                alt={assetName}
                className="modal-preview-img"
                loading="lazy"
                onError={(e) => {
                  console.error("Failed image URL:", e.target.src);
                }}
              />
            ) : asset.mime_type === "application/pdf" ? (
              <iframe
                src={previewUrl}
                className="modal-preview-pdf"
                title={assetName}
              />
            ) : asset.mime_type?.startsWith("video/") ? (
              <video
                src={previewUrl}
                controls
                className="modal-preview-video"
              />
            ) : (
              <div className="modal-preview-placeholder">
                <span>{icon}</span>
                <p>No preview available</p>
              </div>
            )}
          </div>

          {/* RIGHT — DETAILS */}
          <div className="modal-details">
            <p className="modal-description">{description}</p>

            {caption && (
              <div className="modal-detail-group">
                <span className="modal-detail-label">AI Caption</span>
                <span className="modal-detail-value">{caption}</span>
              </div>
            )}

            <div className="modal-detail-group">
              <span className="modal-detail-label">Status</span>
              <span className={"badge " + statusBadge}>{asset.status}</span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Type</span>
              <span className="modal-detail-value">
                {mandatory.asset_type || asset.mime_type}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Owner</span>
              <span className="modal-detail-value">
                {mandatory.owner || "—"}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Created by</span>
              <span className="modal-detail-value">
                {mandatory.created_by || "—"}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Domain</span>
              <span className="modal-detail-value">
                {business.domain || "—"}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Audience</span>
              <span className="modal-detail-value">
                {business.audience || "—"}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Tone</span>
              <span className="modal-detail-value">{content.tone || "—"}</span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Usage Rights</span>
              <span className="modal-detail-value">
                {mandatory.usage_rights || "—"}
              </span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Version</span>
              <span className="modal-detail-value">v{asset.version}</span>
            </div>

            <div className="modal-detail-group">
              <span className="modal-detail-label">Asset ID</span>

              <div className="modal-id-row">
                <code className="modal-id-code">{asset.id}</code>

                <button className="modal-copy-btn" onClick={copyAssetId}>
                  <Copy size={14} />
                </button>
              </div>
            </div>

            {asset.parent_id && (
              <div className="modal-detail-group">
                <span className="modal-detail-label">Parent Asset</span>

                <div className="modal-version-row">
                  <GitBranch size={14} />
                  <code className="modal-id-code">{asset.parent_id}</code>
                </div>
              </div>
            )}

            <div className="modal-detail-group">
              <span className="modal-detail-label">Version Status</span>

              <div className="modal-version-badges">
                <span className={"version-chip " + versionChip}>
                  {versionLabel}
                </span>

                {asset.parent_id && (
                  <span className="version-chip version-chip-versioned">
                    Versioned Asset
                  </span>
                )}
              </div>
            </div>

            {tags.length > 0 && (
              <div className="modal-detail-group">
                <span className="modal-detail-label">AI Tags</span>

                <div className="modal-tags">
                  {tags.map((tag) => (
                    <span key={tag} className="asset-tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button
                className="modal-btn modal-btn-primary"
                onClick={handleDownload}
              >
                <Download size={16} />
                Download
              </button>

              <button
                className="modal-btn modal-btn-secondary"
                onClick={() => {
                  onClose();
                  navigate(`/assets/${asset.id}`);
                }}
              >
                <Eye size={16} />
                Full Details
              </button>

              {asset.mime_type === "application/pdf" && (
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="modal-btn modal-btn-secondary"
                >
                  Open PDF
                </a>
              )}

              {showDelete && onDelete && (
                <button
                  className="modal-btn modal-btn-danger"
                  onClick={onDelete}
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              )}

              {showDelete && !asset.is_archived && (
                <button
                  className="modal-btn modal-btn-archive"
                  onClick={handleArchive}
                  title="Archive this asset"
                >
                  <Archive size={16} />
                  Archive
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetModal;
