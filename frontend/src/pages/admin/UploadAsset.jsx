/**
 * UploadAsset.jsx — Phase 6 Enhanced Upload Wizard
 *
 * New features:
 * 6.1 — Adaptive Business step: conditional required fields per asset_type
 * 6.2 — Drag-and-drop drop zone with onDragOver / onDrop handlers
 * 6.3 — Batch upload: multi-file queue with per-file progress / status
 * 6.4 — Video-specific fields: duration, transcript, aspect_ratio (shown when asset_type = video)
 */
import { useEffect, useState, useContext, useRef, useCallback } from "react";
import {
  Check, UploadCloud, ArrowRight, ArrowLeft, X, GitBranch,
  Film, FileText as FileTextIcon, Layers, AlertCircle, CheckCircle,
  Clock, Trash2
} from "lucide-react";
import api from "../../api/axios";
import Layout from "../../components/common/layout";
import AuthContext from "../../context/AuthContext";
import "../../styles/upload.css";

// ─── Constants ────────────────────────────────────────────────────────────────

const STEPS = ["Upload", "Mandatory", "Business", "Content"];

const ASSET_TYPES = [
  "image", "video", "pdf", "document",
  "banner", "brochure", "case_study", "logo",
  "social_creative", "pitch_deck", "brand_guideline",
  "campaign_file", "testimonial",
];

const VIDEO_TYPES = ["video", "social_creative"];
const CAMPAIGN_REQUIRED_TYPES = ["video", "social_creative", "brochure", "campaign_file"];
const SERVICE_LINE_REQUIRED_TYPES = ["brochure", "campaign_file"];
const AUDIENCE_USE_CASE_REQUIRED_TYPES = ["pitch_deck"];
const DOMAIN_REQUIRED_TYPES = ["logo", "brand_guideline"];
const EXPIRY_RECOMMENDED_TYPES = ["brochure", "campaign_file", "social_creative"];

const ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"];

const USAGE_RIGHTS = [
  { value: "Internal Only",    label: "Internal Only" },
  { value: "Licensed",         label: "Licensed" },
  { value: "Public Domain",    label: "Public Domain" },
  { value: "Restricted",       label: "Restricted" },
  { value: "Royalty Free",     label: "Royalty Free" },
  { value: "Creative Commons", label: "Creative Commons" },
];

const DOMAIN_TYPES = [
  "AI","Staffing","Marketing","Sales","Finance","HR","Operations","Healthcare","Tech","Design",
];
const USE_CASES = [
  "email","presentation","website","campaign","sales","social_media","advertisment",
];
const AUDIENCE_TYPES = ["b2b","enterprise","startup","consumer","partner"];
const FUNNEL_STAGES  = ["awareness","consideration","conversion"];
const TONE_TYPES     = ["professional","casual","formal","friendly","technical","creative"];

// ─── Default form ─────────────────────────────────────────────────────────────

const defaultForm = {
  asset_name: "", asset_type: "image", description: "",
  created_by: "", usage_rights: "Internal Only", owner: "",
  domain: "AI", use_case: "website", audience: "enterprise",
  funnel_stage: "awareness", service_line: "", geography: "",
  campaign: "", language: "", channel: "", expiry_date: "",
  keywords: "", visual_elements: "", tone: "professional", parent_id: "",
  // Video-specific
  video_duration_seconds: "", video_transcript: "", video_aspect_ratio: "16:9",
};

// ─── Batch item states ────────────────────────────────────────────────────────

const BATCH_STATUS = {
  QUEUED: "queued",
  ANALYZING: "analyzing",
  UPLOADING: "uploading",
  DONE: "done",
  ERROR: "error",
};

// ─── Component ────────────────────────────────────────────────────────────────

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

  // Drag-and-drop state
  const [isDragOver, setIsDragOver] = useState(false);
  const dropRef = useRef(null);

  // Batch upload state
  const [batchMode, setBatchMode] = useState(false);
  const [batchQueue, setBatchQueue] = useState([]); // [{file, status, progress, error, assetName}]
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchDone, setBatchDone] = useState(false);

  const { user } = useContext(AuthContext);

  // Pre-fill created_by / owner
  useEffect(() => {
    if (user?.full_name) {
      setForm((prev) => ({
        ...prev,
        created_by: prev.created_by || user.full_name,
        owner: prev.owner || user.full_name,
      }));
    }
  }, [user]);

  // Fetch existing assets for version update
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

  // ─── Helpers ──────────────────────────────────────────────────────────────

  const isVideoType = VIDEO_TYPES.includes(form.asset_type);
  const requiresCampaign = CAMPAIGN_REQUIRED_TYPES.includes(form.asset_type);
  const requiresServiceLine = SERVICE_LINE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresAudienceUseCase = AUDIENCE_USE_CASE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresDomain = DOMAIN_REQUIRED_TYPES.includes(form.asset_type);
  const recommendsExpiry = EXPIRY_RECOMMENDED_TYPES.includes(form.asset_type);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setAiSuggestedFields((prev) => prev.filter((f) => f !== e.target.name));
    setError("");
  };

  // ─── AI Analysis ──────────────────────────────────────────────────────────

  const runAiAnalysis = useCallback(async (selectedFile) => {
    setAnalyzing(true);
    setError("");
    setAiSuggestedFields([]);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await api.post("/assets/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const data = res.data;
      if (data) {
        // All fields the AI may return
        const FIELD_MAP = {
          // Mandatory
          asset_name:   data.asset_name,
          asset_type:   data.asset_type,
          description:  data.description,
          created_by:   data.created_by,
          owner:        data.owner,
          usage_rights: data.usage_rights,
          // Business
          domain:       data.domain,
          use_case:     data.use_case,
          audience:     data.audience,
          funnel_stage: data.funnel_stage,
          // Content
          tone:         data.tone,
          keywords:     data.keywords,
        };

        // Build new form values (only override if AI returned a non-empty value)
        const updates = {};
        const suggestedKeys = [];
        for (const [key, val] of Object.entries(FIELD_MAP)) {
          if (val && String(val).trim()) {
            updates[key] = String(val).trim();
            suggestedKeys.push(key);
          }
        }

        setForm((prev) => ({ ...prev, ...updates }));
        setAiSuggestedFields(suggestedKeys);
        setTimeout(() => setStep(1), 1200);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "AI analysis failed. You can proceed manually.");
    } finally {
      setAnalyzing(false);
    }
  }, []);

  // ─── Single file handler ─────────────────────────────────────────────────

  const handleFileChange = async (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    await runAiAnalysis(selectedFile);
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setAiSuggestedFields([]);
    setForm(defaultForm);
    if (user?.full_name) {
      setForm((prev) => ({ ...prev, created_by: user.full_name, owner: user.full_name }));
    }
  };

  // ─── Drag and Drop (Feature 6.2) ─────────────────────────────────────────

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only fire if leaving the dropzone entirely (not a child)
    if (!dropRef.current?.contains(e.relatedTarget)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length === 0) return;

    if (batchMode) {
      // Add all dropped files to batch queue
      const newItems = droppedFiles.map((f) => ({
        id: crypto.randomUUID(),
        file: f,
        status: BATCH_STATUS.QUEUED,
        progress: 0,
        error: null,
        assetName: f.name.replace(/\.[^/.]+$/, ""),
      }));
      setBatchQueue((prev) => [...prev, ...newItems]);
    } else {
      // Single file mode: use first file only
      handleFileChange(droppedFiles[0]);
    }
  };

  // ─── Batch Upload (Feature 6.3) ──────────────────────────────────────────

  const handleBatchFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const newItems = files.map((f) => ({
      id: crypto.randomUUID(),
      file: f,
      status: BATCH_STATUS.QUEUED,
      progress: 0,
      error: null,
      assetName: f.name.replace(/\.[^/.]+$/, ""),
    }));
    setBatchQueue((prev) => [...prev, ...newItems]);
  };

  const removeBatchItem = (id) => {
    setBatchQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const updateBatchItem = (id, updates) => {
    setBatchQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...updates } : item))
    );
  };

  const runBatchUpload = async () => {
    const queued = batchQueue.filter((i) => i.status === BATCH_STATUS.QUEUED);
    if (queued.length === 0) return;

    setBatchRunning(true);
    setBatchDone(false);

    for (const item of queued) {
      // Step 1: AI Analyze
      updateBatchItem(item.id, { status: BATCH_STATUS.ANALYZING });
      let suggestedName = item.assetName;
      let suggestedType = "image";
      let suggestedDesc = "";
      try {
        const analyzeForm = new FormData();
        analyzeForm.append("file", item.file);
        const aiRes = await api.post("/assets/analyze", analyzeForm, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        suggestedName = aiRes.data?.asset_name || suggestedName;
        suggestedType = aiRes.data?.asset_type || suggestedType;
        suggestedDesc = aiRes.data?.description || "";
      } catch {
        // If AI fails, continue with defaults
      }

      // Step 2: Upload
      updateBatchItem(item.id, { status: BATCH_STATUS.UPLOADING, progress: 10 });
      try {
        const metadata = {
          mandatory: {
            asset_name: suggestedName,
            asset_type: suggestedType,
            description: suggestedDesc || `Batch uploaded: ${item.file.name}`,
            created_by: user?.full_name || "Unknown",
            usage_rights: "Internal Only",
            owner: user?.full_name || "Unknown",
          },
          business: { domain: "AI", use_case: "website", audience: "enterprise", funnel_stage: "awareness" },
          content: { keywords: [], visual_elements: [], tone: "professional" },
        };
        const fd = new FormData();
        fd.append("file", item.file);
        fd.append("metadata", JSON.stringify(metadata));
        await api.post("/assets/upload", fd, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (prog) => {
            const pct = Math.round((prog.loaded / prog.total) * 80) + 10;
            updateBatchItem(item.id, { progress: pct });
          },
        });
        updateBatchItem(item.id, { status: BATCH_STATUS.DONE, progress: 100 });
      } catch (err) {
        const detail = err?.response?.data?.detail;
        const msg = typeof detail === "string" ? detail : "Upload failed";
        updateBatchItem(item.id, { status: BATCH_STATUS.ERROR, error: msg });
      }
    }

    setBatchRunning(false);
    setBatchDone(true);
  };

  // ─── Wizard navigation ────────────────────────────────────────────────────

  const handleNext = () => {
    if (step === 0 && !file) {
      setError("Please select a file to continue.");
      return;
    }
    if (step === 1) {
      if (!form.asset_name || !form.description || !form.created_by || !form.usage_rights || !form.owner) {
        setError("Please fill in all mandatory fields.");
        return;
      }
    }
    if (step === 2) {
      // 6.1 Adaptive validation
      if (requiresCampaign && !form.campaign && !form.service_line) {
        setError(`Asset type "${form.asset_type}" requires Campaign or Service Line.`);
        return;
      }
      if (requiresServiceLine && !form.service_line) {
        setError(`Asset type "${form.asset_type}" requires Service Line.`);
        return;
      }
      if (requiresAudienceUseCase && (!form.audience || !form.use_case)) {
        setError("Pitch decks require both Audience and Use Case.");
        return;
      }
      if (requiresDomain && !form.domain) {
        setError(`Asset type "${form.asset_type}" requires a Domain.`);
        return;
      }
    }
    setError("");
    setStep((s) => s + 1);
  };

  const handleBack = () => { setError(""); setStep((s) => s - 1); };

  // ─── Final Submit ─────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    if (!file) { setError("Please select a file."); return; }

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
        service_line: form.service_line || undefined,
        geography: form.geography || undefined,
        campaign: form.campaign || undefined,
        language: form.language || undefined,
        channel: form.channel || undefined,
        expiry_date: form.expiry_date || undefined,
      },
      content: {
        keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
        visual_elements: form.visual_elements.split(",").map((v) => v.trim()).filter(Boolean),
        tone: form.tone,
      },
    };

    const formData = new FormData();
    formData.append("file", file);
    formData.append("metadata", JSON.stringify(metadata));
    if (isVersionUpdate && selectedParentAsset) {
      formData.append("parent_id", selectedParentAsset.id);
    }
    // Phase 6.4 — Video fields
    if (isVideoType && form.video_duration_seconds) {
      formData.append("video_duration_seconds", form.video_duration_seconds);
    }
    if (isVideoType && form.video_transcript.trim()) {
      formData.append("video_transcript", form.video_transcript);
    }
    if (isVideoType && form.video_aspect_ratio) {
      formData.append("video_aspect_ratio", form.video_aspect_ratio);
    }

    try {
      await api.post("/assets/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSuccess(true);
      setForm(defaultForm);
      setFile(null);
      setStep(0);
      setSelectedParentAsset(null);
      setIsVersionUpdate(false);
      if (user?.full_name) {
        setForm((prev) => ({ ...prev, created_by: user.full_name, owner: user.full_name }));
      }
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

  // ─── Render ───────────────────────────────────────────────────────────────

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
          {/* Batch Mode Toggle */}
          <label className="batch-mode-toggle">
            <input
              type="checkbox"
              checked={batchMode}
              onChange={(e) => {
                setBatchMode(e.target.checked);
                setBatchQueue([]);
                setBatchDone(false);
                setFile(null);
              }}
            />
            <span>Batch Upload</span>
            <span className="batch-mode-badge">
              <Layers size={12} />
              Multi-file
            </span>
          </label>
        </div>

        {/* SUCCESS BANNER */}
        {success && (
          <div className="upload-success">
            <span>Asset uploaded successfully and sent for review!</span>
            <button className="upload-success-close" onClick={() => setSuccess(false)}>
              <X size={16} />
            </button>
          </div>
        )}

        {/* =================== BATCH UPLOAD MODE =================== */}
        {batchMode ? (
          <div className="batch-panel">
            <div
              className={`batch-dropzone ${isDragOver ? "batch-dropzone--drag" : ""}`}
              ref={dropRef}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById("batch-file-input").click()}
            >
              <UploadCloud size={36} />
              <p>Drop multiple files here, or click to select</p>
              <p className="upload-dropzone-hint">All file types supported</p>
            </div>
            <input
              id="batch-file-input"
              type="file"
              multiple
              style={{ display: "none" }}
              onChange={handleBatchFileSelect}
            />

            {batchQueue.length > 0 && (
              <div className="batch-queue">
                <div className="batch-queue-header">
                  <span className="batch-queue-title">
                    Upload Queue — {batchQueue.length} file{batchQueue.length !== 1 ? "s" : ""}
                  </span>
                  {!batchRunning && (
                    <button
                      className="batch-start-btn"
                      onClick={runBatchUpload}
                      disabled={batchQueue.every((i) => i.status !== BATCH_STATUS.QUEUED)}
                    >
                      <UploadCloud size={15} />
                      Upload All
                    </button>
                  )}
                </div>

                {batchQueue.map((item) => (
                  <div
                    key={item.id}
                    className={`batch-item batch-item--${item.status}`}
                  >
                    <div className="batch-item-icon">
                      {item.status === BATCH_STATUS.DONE   && <CheckCircle size={18} />}
                      {item.status === BATCH_STATUS.ERROR  && <AlertCircle size={18} />}
                      {item.status === BATCH_STATUS.QUEUED && <Clock size={18} />}
                      {(item.status === BATCH_STATUS.ANALYZING || item.status === BATCH_STATUS.UPLOADING) && (
                        <div className="batch-spinner" />
                      )}
                    </div>

                    <div className="batch-item-body">
                      <div className="batch-item-name">{item.file.name}</div>
                      <div className="batch-item-meta">
                        {(item.file.size / 1024 / 1024).toFixed(2)} MB
                        {item.status === BATCH_STATUS.ANALYZING && (
                          <span className="batch-status-label batch-status--analyzing">AI Analyzing…</span>
                        )}
                        {item.status === BATCH_STATUS.UPLOADING && (
                          <span className="batch-status-label batch-status--uploading">Uploading {item.progress}%</span>
                        )}
                        {item.status === BATCH_STATUS.DONE && (
                          <span className="batch-status-label batch-status--done">Done — Sent for Review</span>
                        )}
                        {item.status === BATCH_STATUS.ERROR && (
                          <span className="batch-status-label batch-status--error">{item.error}</span>
                        )}
                      </div>
                      {(item.status === BATCH_STATUS.UPLOADING || item.status === BATCH_STATUS.ANALYZING) && (
                        <div className="batch-progress-bar">
                          <div
                            className="batch-progress-fill"
                            style={{ width: `${item.progress}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {item.status === BATCH_STATUS.QUEUED && (
                      <button
                        className="batch-remove-btn"
                        onClick={() => removeBatchItem(item.id)}
                        title="Remove from queue"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}

                {batchDone && (
                  <div className="batch-done-banner">
                    <CheckCircle size={16} />
                    <span>
                      Batch upload complete!{" "}
                      {batchQueue.filter((i) => i.status === BATCH_STATUS.DONE).length} uploaded,{" "}
                      {batchQueue.filter((i) => i.status === BATCH_STATUS.ERROR).length} failed.
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          /* =================== SINGLE UPLOAD WIZARD =================== */
          <div className="upload-wizard">
            {/* STEP INDICATORS */}
            <div className="wizard-steps">
              {STEPS.map((label, i) => (
                <div
                  key={label}
                  className={`wizard-step ${
                    i === step ? "wizard-step--active" : i < step ? "wizard-step--done" : ""
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
              {/* ─────────── STEP 0: UPLOAD ─────────── */}
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

                  {/* SELECT PARENT ASSET */}
                  {isVersionUpdate && (
                    <div className="version-assets">
                      <div className="version-assets-header">
                        <GitBranch size={16} />
                        <span>Select Existing Asset</span>
                      </div>
                      <div className="version-assets-list">
                        {availableAssets.map((a) => {
                          const name = a.asset_metadata?.mandatory?.asset_name || a.original_filename;
                          return (
                            <div
                              key={a.id}
                              className={`version-asset-item ${selectedParentAsset?.id === a.id ? "selected" : ""}`}
                              onClick={() => setSelectedParentAsset(a)}
                            >
                              <div>
                                <strong>{name}</strong>
                                <p>Version {a.version}</p>
                              </div>
                              {a.is_latest && <span className="badge badge-success">Latest</span>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* DROP ZONE — Feature 6.2 */}
                  <div
                    ref={dropRef}
                    className={`upload-dropzone ${file ? "upload-dropzone--filled" : ""} ${
                      analyzing ? "upload-dropzone--analyzing" : ""
                    } ${isDragOver ? "upload-dropzone--drag-over" : ""}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => !analyzing && document.getElementById("file-input").click()}
                  >
                    {analyzing ? (
                      <div className="scanner-container">
                        <div className="scanner-glow" />
                        <div className="btn-loader scanner-loader" />
                        <p className="scanner-text">AI is analyzing your asset to recommend metadata…</p>
                      </div>
                    ) : file ? (
                      <>
                        <div className="upload-dropzone-icon upload-dropzone-icon--success">
                          <Check size={38} />
                        </div>
                        <p className="upload-dropzone-name">{file.name}</p>
                        <p className="upload-dropzone-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        <button className="upload-remove-file" onClick={handleRemoveFile}>Remove</button>
                      </>
                    ) : (
                      <>
                        <div className="upload-dropzone-icon">
                          <UploadCloud size={42} />
                        </div>
                        {isDragOver
                          ? <p className="drop-active-text">Release to upload!</p>
                          : <p>Drag &amp; drop a file here, or click to select</p>
                        }
                        <p className="upload-dropzone-hint">All file types supported</p>
                      </>
                    )}
                  </div>

                  <input
                    id="file-input"
                    type="file"
                    style={{ display: "none" }}
                    onChange={(e) => handleFileChange(e.target.files[0])}
                  />

                  {file && (
                    <div className="upload-summary">
                      <h3>File Details</h3>
                      <div className="summary-row">
                        <span>Filename</span><span>{file.name}</span>
                      </div>
                      <div className="summary-row">
                        <span>Size</span><span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                      {selectedParentAsset && (
                        <div className="summary-row summary-row-version">
                          <span>Updating Version Of</span>
                          <span>
                            {selectedParentAsset.asset_metadata?.mandatory?.asset_name ||
                              selectedParentAsset.original_filename}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ─────────── STEP 1: MANDATORY ─────────── */}
              {step === 1 && (
                <div className="wizard-fields">
                  <h2 className="wizard-section-title">Mandatory Information (AI Recommended)</h2>

                  <Field label="Asset Name *" ai={aiSuggestedFields.includes("asset_name")}>
                    <input name="asset_name" value={form.asset_name} onChange={handleChange}
                      placeholder="e.g. Marketing Banner"
                      className={aiSuggestedFields.includes("asset_name") ? "ai-recommended-input" : ""} />
                  </Field>

                  <Field label="Asset Type *" ai={aiSuggestedFields.includes("asset_type")}>
                    <select name="asset_type" value={form.asset_type} onChange={handleChange}
                      className={aiSuggestedFields.includes("asset_type") ? "ai-recommended-input" : ""}>
                      {ASSET_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </Field>

                  {/* 6.4 — Video indicator */}
                  {isVideoType && (
                    <div className="video-type-notice">
                      <Film size={14} />
                      Video-specific fields (duration, transcript, aspect ratio) will be available in the Business step.
                    </div>
                  )}

                  <Field label="Description *" ai={aiSuggestedFields.includes("description")}>
                    <textarea name="description" value={form.description} onChange={handleChange} rows={3}
                      className={aiSuggestedFields.includes("description") ? "ai-recommended-input" : ""} />
                  </Field>

                  <div className="upload-row">
                    <Field label="Created By *" ai={aiSuggestedFields.includes("created_by")}>
                      <input name="created_by" value={form.created_by} onChange={handleChange}
                        className={aiSuggestedFields.includes("created_by") ? "ai-recommended-input" : ""} />
                    </Field>
                    <Field label="Owner *" ai={aiSuggestedFields.includes("owner")}>
                      <input name="owner" value={form.owner} onChange={handleChange}
                        className={aiSuggestedFields.includes("owner") ? "ai-recommended-input" : ""} />
                    </Field>
                  </div>

                  <Field label="Usage Rights *" ai={aiSuggestedFields.includes("usage_rights")}>
                    <select name="usage_rights" value={form.usage_rights} onChange={handleChange}
                      className={aiSuggestedFields.includes("usage_rights") ? "ai-recommended-input" : ""}>
                      {USAGE_RIGHTS.map(({ value, label }) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </Field>
                </div>
              )}

              {/* ─────────── STEP 2: BUSINESS (Adaptive — Feature 6.1) ─────────── */}
              {step === 2 && (
                <div className="wizard-fields">
                  <h2 className="wizard-section-title">
                    Business Metadata
                    {aiSuggestedFields.some((f) =>
                      ["domain", "use_case", "audience", "funnel_stage"].includes(f)
                    ) && <span className="ai-badge ai-badge--step">AI Recommended</span>}
                    <span className="adaptive-badge">
                      Adapted for: <strong>{form.asset_type}</strong>
                    </span>
                  </h2>

                  {/* Required fields indicator */}
                  {(requiresCampaign || requiresServiceLine || requiresAudienceUseCase || requiresDomain) && (
                    <div className="adaptive-rules-notice">
                      <AlertCircle size={14} />
                      <span>
                        <strong>{form.asset_type}</strong> requires:
                        {requiresDomain && " Domain"}
                        {requiresCampaign && " Campaign or Service Line"}
                        {requiresServiceLine && " + Service Line"}
                        {requiresAudienceUseCase && " Audience + Use Case"}
                      </span>
                    </div>
                  )}

                  {/* Domain — always shown, required for logo/brand_guideline */}
                  <div className="upload-row">
                    <Field label={`Domain${requiresDomain ? " *" : ""}`} ai={aiSuggestedFields.includes("domain")}>
                      <select name="domain" value={form.domain} onChange={handleChange}
                        className={aiSuggestedFields.includes("domain") ? "ai-recommended-input" : ""}>
                        {DOMAIN_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </Field>

                    <Field label={`Use Case${requiresAudienceUseCase ? " *" : ""}`} ai={aiSuggestedFields.includes("use_case")}>
                      <select name="use_case" value={form.use_case} onChange={handleChange}
                        className={aiSuggestedFields.includes("use_case") ? "ai-recommended-input" : ""}>
                        {USE_CASES.map((u) => <option key={u} value={u}>{u}</option>)}
                      </select>
                    </Field>
                  </div>

                  <div className="upload-row">
                    <Field label={`Audience${requiresAudienceUseCase ? " *" : ""}`} ai={aiSuggestedFields.includes("audience")}>
                      <select name="audience" value={form.audience} onChange={handleChange}
                        className={aiSuggestedFields.includes("audience") ? "ai-recommended-input" : ""}>
                        {AUDIENCE_TYPES.map((a) => <option key={a} value={a}>{a}</option>)}
                      </select>
                    </Field>

                    <Field label="Funnel Stage" ai={aiSuggestedFields.includes("funnel_stage")}>
                      <select name="funnel_stage" value={form.funnel_stage} onChange={handleChange}
                        className={aiSuggestedFields.includes("funnel_stage") ? "ai-recommended-input" : ""}>
                        {FUNNEL_STAGES.map((f) => <option key={f} value={f}>{f}</option>)}
                      </select>
                    </Field>
                  </div>

                  {/* Campaign — highlighted if required */}
                  <div className="upload-row">
                    <Field label={`Campaign${requiresCampaign ? " *" : ""}`} required={requiresCampaign}>
                      <input name="campaign" value={form.campaign} onChange={handleChange}
                        placeholder="e.g. Summer 2026 Campaign"
                        className={requiresCampaign && !form.campaign ? "field-required-highlight" : ""} />
                    </Field>
                    <Field label={`Service Line${requiresServiceLine ? " *" : ""}`} required={requiresServiceLine}>
                      <input name="service_line" value={form.service_line} onChange={handleChange}
                        placeholder="e.g. Enterprise Sales"
                        className={requiresServiceLine && !form.service_line ? "field-required-highlight" : ""} />
                    </Field>
                  </div>

                  <div className="upload-row">
                    <Field label="Geography">
                      <input name="geography" value={form.geography} onChange={handleChange}
                        placeholder="e.g. North America" />
                    </Field>
                    <Field label="Language">
                      <input name="language" value={form.language} onChange={handleChange}
                        placeholder="e.g. English" />
                    </Field>
                  </div>

                  <div className="upload-row">
                    <Field label="Channel">
                      <input name="channel" value={form.channel} onChange={handleChange}
                        placeholder="e.g. LinkedIn, Email" />
                    </Field>
                    <Field label={`Expiry Date${recommendsExpiry ? " (recommended)" : ""}`}>
                      <input type="date" name="expiry_date" value={form.expiry_date} onChange={handleChange}
                        className={recommendsExpiry && !form.expiry_date ? "field-recommended-highlight" : ""} />
                    </Field>
                  </div>

                  {/* ─── Video-specific fields — Feature 6.4 ─── */}
                  {isVideoType && (
                    <div className="video-fields-section">
                      <div className="video-fields-header">
                        <Film size={16} />
                        <span>Video Details</span>
                      </div>

                      <div className="upload-row">
                        <Field label="Duration (seconds)">
                          <input type="number" name="video_duration_seconds"
                            value={form.video_duration_seconds} onChange={handleChange}
                            min="0" placeholder="e.g. 90" />
                        </Field>
                        <Field label="Aspect Ratio">
                          <select name="video_aspect_ratio" value={form.video_aspect_ratio} onChange={handleChange}>
                            {ASPECT_RATIOS.map((r) => <option key={r} value={r}>{r}</option>)}
                          </select>
                        </Field>
                      </div>

                      <Field label="Transcript / Captions (optional)">
                        <textarea name="video_transcript" value={form.video_transcript}
                          onChange={handleChange} rows={4}
                          placeholder="Paste video transcript or captions here…" />
                      </Field>
                    </div>
                  )}
                </div>
              )}

              {/* ─────────── STEP 3: CONTENT ─────────── */}
              {step === 3 && (
                <div className="wizard-fields">
                  <h2 className="wizard-section-title">Content Metadata</h2>

                  <Field label="Keywords" ai={aiSuggestedFields.includes("keywords")}>
                    <input name="keywords" value={form.keywords} onChange={handleChange}
                      placeholder="marketing, brand, summer — comma separated"
                      className={aiSuggestedFields.includes("keywords") ? "ai-recommended-input" : ""} />
                  </Field>

                  <Field label="Visual Elements">
                    <input name="visual_elements" value={form.visual_elements} onChange={handleChange}
                      placeholder="logo, person, outdoor — comma separated" />
                  </Field>

                  <Field label="Tone" ai={aiSuggestedFields.includes("tone")}>
                    <select name="tone" value={form.tone} onChange={handleChange}
                      className={aiSuggestedFields.includes("tone") ? "ai-recommended-input" : ""}>
                      {TONE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </Field>

                  {/* Final Summary */}
                  <div className="upload-summary">
                    <h3>Asset Summary</h3>
                    <div className="summary-row"><span>Filename</span><span>{file?.name}</span></div>
                    <div className="summary-row"><span>Asset Name</span><span>{form.asset_name}</span></div>
                    <div className="summary-row"><span>Type</span><span>{form.asset_type}</span></div>
                    <div className="summary-row"><span>Domain</span><span>{form.domain}</span></div>
                    {form.campaign && <div className="summary-row"><span>Campaign</span><span>{form.campaign}</span></div>}
                    {isVideoType && form.video_duration_seconds && (
                      <div className="summary-row">
                        <span>Video Duration</span>
                        <span>{form.video_duration_seconds}s ({Math.floor(form.video_duration_seconds / 60)}m {form.video_duration_seconds % 60}s)</span>
                      </div>
                    )}
                    {selectedParentAsset && (
                      <div className="summary-row summary-row-version">
                        <span>Updating Version Of</span>
                        <span>
                          {selectedParentAsset.asset_metadata?.mandatory?.asset_name ||
                            selectedParentAsset.original_filename}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {error && <div className="auth-error">{error}</div>}

              <div className="wizard-nav">
                {step > 0 && (
                  <button className="wizard-btn-back" onClick={handleBack} disabled={loading}>
                    <ArrowLeft size={16} />Back
                  </button>
                )}
                {step < STEPS.length - 1 ? (
                  <button className="wizard-btn-next" onClick={handleNext}>
                    Next<ArrowRight size={16} />
                  </button>
                ) : (
                  <button className="wizard-btn-submit" onClick={handleSubmit} disabled={loading}>
                    {loading ? <span className="btn-loader" /> : <><UploadCloud size={16} />Upload Asset</>}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

// ─── Helper field wrapper ──────────────────────────────────────────────────────

const Field = ({ label, ai, children }) => (
  <div className="form-group">
    <label>
      {label}
      {ai && <span className="ai-badge">AI Suggested</span>}
    </label>
    {children}
  </div>
);

export default UploadAsset;
