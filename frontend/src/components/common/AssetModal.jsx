import { useEffect } from "react";

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
  // Sparkles,
} from "lucide-react";

// import { useNavigate } from "react-router-dom";

import api from "../../api/axios";

import "../../styles/assetmodal.css";

const TYPE_ICON = {
  "image/jpeg": <Image size={22} className="modal-file-icon image" />,

  "image/png": <Image size={22} className="modal-file-icon image" />,

  "video/mp4": <Video size={22} className="modal-file-icon video" />,

  "application/pdf": <FileText size={22} className="modal-file-icon pdf" />,
};

const AssetModal = ({ asset, onClose, onDelete, showDelete }) => {
  // const navigate = useNavigate();

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

  // CLOSE ON ESC

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

  // COPY ASSET ID

  const copyAssetId = async () => {
    try {
      await navigator.clipboard.writeText(asset.id);

      alert("Asset ID copied!");
    } catch {
      alert("Failed to copy asset ID");
    }
  };

  // DOWNLOAD HANDLER

  const handleDownload = async () => {
    try {
      // LOCAL FILES

      if (!asset.storage_path?.startsWith("http")) {
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

        return;
      }

      // CLOUDINARY FILES

      const link = document.createElement("a");

      link.href = asset.storage_path;

      link.target = "_blank";

      link.setAttribute("download", asset.original_filename);

      document.body.appendChild(link);

      link.click();

      link.remove();
    } catch (err) {
      console.error(err);

      alert("Download failed. Please try again.");
    }
  };

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
                src={`http://localhost:8000/assets/${asset.id}/preview`}
                alt={assetName}
                className="modal-preview-img"
              />
            ) : asset.mime_type === "application/pdf" ? (
              <iframe
                src={`http://localhost:8000/assets/${asset.id}/pdf-viewer`}
                className="modal-preview-pdf"
                title={assetName}
              />
            ) : asset.mime_type?.startsWith("video/") ? (
              <video
                src={`http://localhost:8000/assets/${asset.id}/download`}
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

              <span
                className={`badge ${
                  asset.status === "approved"
                    ? "badge-success"
                    : asset.status === "rejected"
                      ? "badge-danger"
                      : "badge-warning"
                }`}
              >
                {asset.status}
              </span>
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

            {/* ASSET ID */}

            <div className="modal-detail-group">
              <span className="modal-detail-label">Asset ID</span>

              <div className="modal-id-row">
                <code className="modal-id-code">{asset.id}</code>

                <button className="modal-copy-btn" onClick={copyAssetId}>
                  <Copy size={14} />
                </button>
              </div>
            </div>

            {/* PARENT ASSET */}

            {asset.parent_id && (
              <div className="modal-detail-group">
                <span className="modal-detail-label">Parent Asset</span>

                <div className="modal-version-row">
                  <GitBranch size={14} />

                  <code className="modal-id-code">{asset.parent_id}</code>
                </div>
              </div>
            )}

            {/* VERSION STATUS */}

            <div className="modal-detail-group">
              <span className="modal-detail-label">Version Status</span>

              <div className="modal-version-badges">
                <span
                  className={`version-chip ${
                    asset.is_latest ? "version-chip-latest" : "version-chip-old"
                  }`}
                >
                  {asset.is_latest ? "Latest Version" : "Outdated Version"}
                </span>

                {asset.parent_id && (
                  <span className="version-chip version-chip-versioned">
                    Versioned Asset
                  </span>
                )}
              </div>
            </div>

            {/* TAGS */}

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

            {/* ACTIONS */}

            <div className="modal-actions">
              <button
                className="modal-btn modal-btn-primary"
                onClick={handleDownload}
              >
                <Download size={16} />
                Download
              </button>

              {/* <button
                className="modal-btn modal-btn-version"
                onClick={() => navigate(`/admin/upload?parent_id=${asset.id}`)}
              >
                <Sparkles size={16} />
                Upload New Version
              </button> */}

              {asset.mime_type === "application/pdf" && (
                <a
                  href={`http://localhost:8000/assets/${asset.id}/pdf-viewer`}
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetModal;
