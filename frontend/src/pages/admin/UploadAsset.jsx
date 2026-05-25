import { useState } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import "../../styles/upload.css";

const STEPS = ["Mandatory", "Business", "Content", "Upload"];

const ASSET_TYPES = ["image", "video", "pdf", "document", "other"];

const DOMAIN_TYPES = [
  "AI",
  "Marketing",
  "Sales",
  "HR",
  "Finance",
  "Tech",
  "Design",
  "Other",
];

const USE_CASES = [
  "website",
  "social_media",
  "email",
  "presentation",
  "internal",
  "advertisement",
  "other",
];

const AUDIENCE_TYPES = [
  "enterprise",
  "consumer",
  "internal",
  "partner",
  "public",
];

const FUNNEL_STAGES = ["awareness", "consideration", "decision", "retention"];

const TONE_TYPES = [
  "professional",
  "casual",
  "formal",
  "friendly",
  "technical",
  "creative",
];

const defaultForm = {
  asset_name: "",
  asset_type: "image",
  description: "",
  created_by: "",
  usage_rights: "",
  owner: "",
  domain: "AI",
  use_case: "website",
  audience: "enterprise",
  funnel_stage: "awareness",
  keywords: "",
  visual_elements: "",
  tone: "professional",
};

const UploadAsset = () => {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(defaultForm);
  const [file, setFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });

    setError("");
  };

  const handleNext = () => {
    if (step === 0) {
      if (
        !form.asset_name ||
        !form.description ||
        !form.created_by ||
        !form.usage_rights ||
        !form.owner
      ) {
        setError("Please fill in all mandatory fields.");
        return;
      }
    }

    setError("");
    setStep((s) => s + 1);
  };

  const handleBack = () => {
    setError("");
    setStep((s) => s - 1);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please select a file.");
      return;
    }

    setLoading(true);
    setError("");

    const metadata = {
      mandatory: {
        asset_name: form.asset_name,
        asset_type: form.asset_type,
        description: form.description,
        created_by: form.created_by,
        usage_rights: form.usage_rights,
        owner: form.owner,
      },

      business: {
        domain: form.domain,
        use_case: form.use_case,
        audience: form.audience,
        funnel_stage: form.funnel_stage,
      },

      content: {
        keywords: form.keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),

        visual_elements: form.visual_elements
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),

        tone: form.tone,
      },
    };

    const formData = new FormData();

    formData.append("file", file);
    formData.append("metadata", JSON.stringify(metadata));

    try {
      await api.post("/assets/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSuccess(true);
      setForm(defaultForm);
      setFile(null);
      setStep(0);
    } catch (err) {
      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
        // FastAPI / Pydantic validation errors
        setError(detail.map((e) => e.msg).join(", "));
      } else {
        setError(detail || "Upload failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="upload-page">
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Upload Asset</h1>

            <p className="admin-subtitle">
              Fill in asset details and upload your file
            </p>
          </div>
        </div>

        {success && (
          <div className="upload-success">
            Asset uploaded successfully and sent for review!
            <button
              className="upload-success-close"
              onClick={() => setSuccess(false)}
            >
              ✕
            </button>
          </div>
        )}

        <div className="upload-wizard">
          {/* STEP INDICATORS */}
          <div className="wizard-steps">
            {STEPS.map((label, i) => (
              <div
                key={label}
                className={`wizard-step ${
                  i === step
                    ? "wizard-step--active"
                    : i < step
                      ? "wizard-step--done"
                      : ""
                }`}
              >
                <div className="wizard-step-num">{i < step ? "✓" : i + 1}</div>

                <span className="wizard-step-label">{label}</span>
              </div>
            ))}
          </div>

          <div className="wizard-body">
            {/* STEP 0 — MANDATORY */}
            {step === 0 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Mandatory Information</h2>

                <div className="form-group">
                  <label>Asset Name *</label>

                  <input
                    name="asset_name"
                    value={form.asset_name}
                    onChange={handleChange}
                    placeholder="e.g. Q1 Marketing Banner"
                  />
                </div>

                <div className="form-group">
                  <label>Asset Type *</label>

                  <select
                    name="asset_type"
                    value={form.asset_type}
                    onChange={handleChange}
                  >
                    {ASSET_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Description *</label>

                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="Describe what this asset is used for..."
                    rows={3}
                  />
                </div>

                <div className="upload-row">
                  <div className="form-group">
                    <label>Created By *</label>

                    <input
                      name="created_by"
                      value={form.created_by}
                      onChange={handleChange}
                      placeholder="Your name"
                    />
                  </div>

                  <div className="form-group">
                    <label>Owner *</label>

                    <input
                      name="owner"
                      value={form.owner}
                      onChange={handleChange}
                      placeholder="e.g. Marketing Team"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Usage Rights *</label>

                  <input
                    name="usage_rights"
                    value={form.usage_rights}
                    onChange={handleChange}
                    placeholder="e.g. internal, commercial, restricted"
                  />
                </div>
              </div>
            )}

            {/* STEP 1 — BUSINESS */}
            {step === 1 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Business Metadata</h2>

                <div className="upload-row">
                  <div className="form-group">
                    <label>Domain</label>

                    <select
                      name="domain"
                      value={form.domain}
                      onChange={handleChange}
                    >
                      {DOMAIN_TYPES.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Use Case</label>

                    <select
                      name="use_case"
                      value={form.use_case}
                      onChange={handleChange}
                    >
                      {USE_CASES.map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="upload-row">
                  <div className="form-group">
                    <label>Audience</label>

                    <select
                      name="audience"
                      value={form.audience}
                      onChange={handleChange}
                    >
                      {AUDIENCE_TYPES.map((a) => (
                        <option key={a} value={a}>
                          {a}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Funnel Stage</label>

                    <select
                      name="funnel_stage"
                      value={form.funnel_stage}
                      onChange={handleChange}
                    >
                      {FUNNEL_STAGES.map((f) => (
                        <option key={f} value={f}>
                          {f}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2 — CONTENT */}
            {step === 2 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Content Metadata</h2>

                <div className="form-group">
                  <label>Keywords</label>

                  <input
                    name="keywords"
                    value={form.keywords}
                    onChange={handleChange}
                    placeholder="AI, dashboard, analytics (comma separated)"
                  />
                </div>

                <div className="form-group">
                  <label>Visual Elements</label>

                  <input
                    name="visual_elements"
                    value={form.visual_elements}
                    onChange={handleChange}
                    placeholder="charts, UI, icons (comma separated)"
                  />
                </div>

                <div className="form-group">
                  <label>Tone</label>

                  <select name="tone" value={form.tone} onChange={handleChange}>
                    {TONE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* STEP 3 — FILE */}
            {step === 3 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Upload File</h2>

                <div
                  className={`upload-dropzone ${
                    file ? "upload-dropzone--filled" : ""
                  }`}
                  onClick={() => document.getElementById("file-input").click()}
                >
                  {file ? (
                    <>
                      <span className="upload-dropzone-icon">✅</span>

                      <p className="upload-dropzone-name">{file.name}</p>

                      <p className="upload-dropzone-size">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>

                      <button
                        className="upload-remove-file"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFile(null);
                        }}
                      >
                        Remove
                      </button>
                    </>
                  ) : (
                    <>
                      <span className="upload-dropzone-icon">📁</span>

                      <p>Click to select a file</p>

                      <p className="upload-dropzone-hint">
                        Supported: JPEG, PNG, MP4, PDF
                      </p>
                    </>
                  )}
                </div>

                <input
                  id="file-input"
                  type="file"
                  accept="image/jpeg,image/png,video/mp4,application/pdf"
                  style={{ display: "none" }}
                  onChange={(e) => setFile(e.target.files[0])}
                />

                <div className="upload-summary">
                  <h3>Summary</h3>

                  <div className="summary-row">
                    <span>Asset Name</span>
                    <span>{form.asset_name}</span>
                  </div>

                  <div className="summary-row">
                    <span>Type</span>
                    <span>{form.asset_type}</span>
                  </div>

                  <div className="summary-row">
                    <span>Domain</span>
                    <span>{form.domain}</span>
                  </div>

                  <div className="summary-row">
                    <span>Owner</span>
                    <span>{form.owner}</span>
                  </div>

                  <div className="summary-row">
                    <span>Tone</span>
                    <span>{form.tone}</span>
                  </div>
                </div>
              </div>
            )}

            {error && <div className="auth-error">{error}</div>}

            <div className="wizard-nav">
              {step > 0 && (
                <button className="wizard-btn-back" onClick={handleBack}>
                  ← Back
                </button>
              )}

              {step < STEPS.length - 1 ? (
                <button className="wizard-btn-next" onClick={handleNext}>
                  Next →
                </button>
              ) : (
                <button
                  className="wizard-btn-submit"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? <span className="btn-loader" /> : "Upload Asset"}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default UploadAsset;
