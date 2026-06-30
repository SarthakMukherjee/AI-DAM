import { useEffect, useState } from "react";

import {
  Check,
  UploadCloud,
  ArrowRight,
  ArrowLeft,
  X,
  GitBranch,
} from "lucide-react";

import api from "../../api/axios";

import Layout from "../../components/common/layout";

import "../../styles/upload.css";

const STEPS = ["Upload", "Mandatory", "Business", "Content"];

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
  "advertisement",
  "other",
];

const AUDIENCE_TYPES = [
  "enterprise",
  "consumer",
  "startup",
  "partner",
  "public",
  "b2b",
];

const FUNNEL_STAGES = [
  "awareness",
  "consideration",
  "decision",
  "retention",
  "conversion",
];

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

  parent_id: "",
};

const UploadAsset = () => {
  const [step, setStep] = useState(0);

  const [form, setForm] = useState(defaultForm);

  const [file, setFile] = useState(null);

  const [loading, setLoading] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);

  const [success, setSuccess] = useState(false);

  const [error, setError] = useState("");

  const [isVersionUpdate, setIsVersionUpdate] = useState(false);

  const [availableAssets, setAvailableAssets] = useState([]);

  const [selectedParentAsset, setSelectedParentAsset] = useState(null);

  const [aiSuggestedFields, setAiSuggestedFields] = useState([]);

  // FETCH ASSETS

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await api.get("/assets");

        setAvailableAssets(res.data || []);
      } catch (err) {
        console.error(err);
      }
    };

    fetchAssets();
  }, []);

  const handleChange = (e) => {
    setForm({
      ...form,

      [e.target.name]: e.target.value,
    });

    setAiSuggestedFields((prev) =>
      prev.filter((field) => field !== e.target.name)
    );

    setError("");
  };

  const handleFileChange = async (selectedFile) => {
    if (!selectedFile) return;

    setFile(selectedFile);

    setAnalyzing(true);

    setError("");

    setAiSuggestedFields([]);

    const formData = new FormData();

    formData.append("file", selectedFile);

    try {
      const res = await api.post("/assets/analyze", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const data = res.data;

      if (data) {
        setForm((prev) => ({
          ...prev,

          asset_name: data.asset_name || prev.asset_name,

          asset_type: data.asset_type || prev.asset_type,

          description: data.description || prev.description,

          created_by: data.created_by || prev.created_by,

          owner: data.owner || prev.owner,

          usage_rights: data.usage_rights || prev.usage_rights,
        }));

        const suggestedKeys = [];

        if (data.asset_name) suggestedKeys.push("asset_name");

        if (data.asset_type) suggestedKeys.push("asset_type");

        if (data.description) suggestedKeys.push("description");

        if (data.created_by) suggestedKeys.push("created_by");

        if (data.owner) suggestedKeys.push("owner");

        if (data.usage_rights) suggestedKeys.push("usage_rights");

        setAiSuggestedFields(suggestedKeys);

        // Auto advance to next step to review suggestions

        setTimeout(() => {
          setStep(1);
        }, 1200);
      }
    } catch (err) {
      console.error(err);

      const detail = err?.response?.data?.detail;

      setError(
        detail ||
          "AI analysis failed. You can proceed with filling metadata manually."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();

    setFile(null);

    setAiSuggestedFields([]);

    setForm(defaultForm);
  };

  const handleNext = () => {
    if (step === 0) {
      if (!file) {
        setError("Please select a file to continue.");

        return;
      }
    }

    if (step === 1) {
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

    if (isVersionUpdate && selectedParentAsset) {
      formData.append("parent_id", selectedParentAsset.id);
    }

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

      setSelectedParentAsset(null);

      setIsVersionUpdate(false);
    } catch (err) {
      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
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
              Ingest a new asset with automatic AI metadata suggestions
            </p>
          </div>
        </div>

        {success && (
          <div className="upload-success">
            <span>Asset uploaded successfully and sent for review!</span>

            <button
              className="upload-success-close"
              onClick={() => setSuccess(false)}
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="upload-wizard">
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
                <div className="wizard-step-num">
                  {i < step ? <Check size={14} /> : i + 1}
                </div>

                <span className="wizard-step-label">{label}</span>
              </div>
            ))}
          </div>

          <div className="wizard-body">
            {/* STEP 0 - UPLOAD */}

            {step === 0 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Upload File</h2>

                {/* VERSION TOGGLE */}

                <div className="version-toggle">
                  <label className="version-checkbox">
                    <input
                      type="checkbox"
                      checked={isVersionUpdate}
                      onChange={(e) => setIsVersionUpdate(e.target.checked)}
                    />

                    <span>Upload as new version</span>
                  </label>
                </div>

                {/* SELECT ASSET */}

                {isVersionUpdate && (
                  <div className="version-assets">
                    <div className="version-assets-header">
                      <GitBranch size={16} />

                      <span>Select Existing Asset</span>
                    </div>

                    <div className="version-assets-list">
                      {availableAssets.map((a) => {
                        const name =
                          a.asset_metadata?.mandatory?.asset_name ||
                          a.original_filename;

                        return (
                          <div
                            key={a.id}
                            className={`version-asset-item ${
                              selectedParentAsset?.id === a.id ? "selected" : ""
                            }`}
                            onClick={() => {
                              setSelectedParentAsset(a);
                            }}
                          >
                            <div>
                              <strong>{name}</strong>

                              <p>Version {a.version}</p>
                            </div>

                            {a.is_latest && (
                              <span className="badge badge-success">
                                Latest
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* DROPZONE */}

                <div
                  className={`upload-dropzone ${
                    file ? "upload-dropzone--filled" : ""
                  } ${analyzing ? "upload-dropzone--analyzing" : ""}`}
                  onClick={() =>
                    !analyzing && document.getElementById("file-input").click()
                  }
                >
                  {analyzing ? (
                    <div className="scanner-container">
                      <div className="scanner-glow"></div>

                      <div className="btn-loader scanner-loader"></div>

                      <p className="scanner-text">
                        AI is analyzing your asset to recommend metadata...
                      </p>
                    </div>
                  ) : file ? (
                    <>
                      <div className="upload-dropzone-icon upload-dropzone-icon--success">
                        <Check size={38} />
                      </div>

                      <p className="upload-dropzone-name">{file.name}</p>

                      <p className="upload-dropzone-size">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>

                      <button
                        className="upload-remove-file"
                        onClick={handleRemoveFile}
                      >
                        Remove
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="upload-dropzone-icon">
                        <UploadCloud size={42} />
                      </div>

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
                  style={{
                    display: "none",
                  }}
                  onChange={(e) => handleFileChange(e.target.files[0])}
                />

                {/* SUMMARY */}

                {file && (
                  <div className="upload-summary">
                    <h3>File Details</h3>

                    <div className="summary-row">
                      <span>Filename</span>

                      <span>{file.name}</span>
                    </div>

                    <div className="summary-row">
                      <span>Size</span>

                      <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>

                    {selectedParentAsset && (
                      <div className="summary-row summary-row-version">
                        <span>Updating Version Of</span>

                        <span>
                          {selectedParentAsset.asset_metadata?.mandatory
                            ?.asset_name ||
                            selectedParentAsset.original_filename}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* STEP 1 - MANDATORY */}

            {step === 1 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">
                  Mandatory Information (AI Recommended)
                </h2>

                <div className="form-group">
                  <label>
                    Asset Name *
                    {aiSuggestedFields.includes("asset_name") && (
                      <span className="ai-badge">AI Suggested</span>
                    )}
                  </label>

                  <input
                    name="asset_name"
                    value={form.asset_name}
                    onChange={handleChange}
                    placeholder="e.g. Marketing Banner"
                    className={
                      aiSuggestedFields.includes("asset_name")
                        ? "ai-recommended-input"
                        : ""
                    }
                  />
                </div>

                <div className="form-group">
                  <label>
                    Asset Type *
                    {aiSuggestedFields.includes("asset_type") && (
                      <span className="ai-badge">AI Suggested</span>
                    )}
                  </label>

                  <select
                    name="asset_type"
                    value={form.asset_type}
                    onChange={handleChange}
                    className={
                      aiSuggestedFields.includes("asset_type")
                        ? "ai-recommended-input"
                        : ""
                    }
                  >
                    {ASSET_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>
                    Description *
                    {aiSuggestedFields.includes("description") && (
                      <span className="ai-badge">AI Suggested</span>
                    )}
                  </label>

                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    rows={3}
                    className={
                      aiSuggestedFields.includes("description")
                        ? "ai-recommended-input"
                        : ""
                    }
                  />
                </div>

                <div className="upload-row">
                  <div className="form-group">
                    <label>
                      Created By *
                      {aiSuggestedFields.includes("created_by") && (
                        <span className="ai-badge">AI Suggested</span>
                      )}
                    </label>

                    <input
                      name="created_by"
                      value={form.created_by}
                      onChange={handleChange}
                      className={
                        aiSuggestedFields.includes("created_by")
                          ? "ai-recommended-input"
                          : ""
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>
                      Owner *
                      {aiSuggestedFields.includes("owner") && (
                        <span className="ai-badge">AI Suggested</span>
                      )}
                    </label>

                    <input
                      name="owner"
                      value={form.owner}
                      onChange={handleChange}
                      className={
                        aiSuggestedFields.includes("owner")
                          ? "ai-recommended-input"
                          : ""
                      }
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>
                    Usage Rights *
                    {aiSuggestedFields.includes("usage_rights") && (
                      <span className="ai-badge">AI Suggested</span>
                    )}
                  </label>

                  <input
                    name="usage_rights"
                    value={form.usage_rights}
                    onChange={handleChange}
                    className={
                      aiSuggestedFields.includes("usage_rights")
                        ? "ai-recommended-input"
                        : ""
                    }
                  />
                </div>
              </div>
            )}

            {/* STEP 2 - BUSINESS */}

            {step === 2 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Business Metadata</h2>

                {/* DOMAIN + USE CASE */}

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

                {/* AUDIENCE + FUNNEL STAGE */}

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

            {/* STEP 3 - CONTENT */}

            {step === 3 && (
              <div className="wizard-fields">
                <h2 className="wizard-section-title">Content Metadata</h2>

                <div className="form-group">
                  <label>Keywords</label>

                  <input
                    name="keywords"
                    value={form.keywords}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label>Visual Elements</label>

                  <input
                    name="visual_elements"
                    value={form.visual_elements}
                    onChange={handleChange}
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

                {/* SUMMARY */}

                <div className="upload-summary">
                  <h3>Asset Summary</h3>

                  <div className="summary-row">
                    <span>Filename</span>

                    <span>{file?.name}</span>
                  </div>

                  <div className="summary-row">
                    <span>Asset Name</span>

                    <span>{form.asset_name}</span>
                  </div>

                  <div className="summary-row">
                    <span>Type</span>

                    <span>{form.asset_type}</span>
                  </div>

                  {selectedParentAsset && (
                    <div className="summary-row summary-row-version">
                      <span>Updating Version Of</span>

                      <span>
                        {selectedParentAsset.asset_metadata?.mandatory
                          ?.asset_name || selectedParentAsset.original_filename}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {error && <div className="auth-error">{error}</div>}

            <div className="wizard-nav">
              {step > 0 && (
                <button
                  className="wizard-btn-back"
                  onClick={handleBack}
                  disabled={loading}
                >
                  <ArrowLeft size={16} />
                  Back
                </button>
              )}

              {step < STEPS.length - 1 ? (
                <button className="wizard-btn-next" onClick={handleNext}>
                  Next
                  <ArrowRight size={16} />
                </button>
              ) : (
                <button
                  className="wizard-btn-submit"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? (
                    <span className="btn-loader" />
                  ) : (
                    <>
                      <UploadCloud size={16} />
                      Upload Asset
                    </>
                  )}
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
