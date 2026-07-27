import React, { useState } from "react";
import { X, CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Film } from "lucide-react";

const STEPS = ["Mandatory", "Business", "Content"];

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

// ─── Field wrapper — matches single-upload Field with AI badge support ────────
const Field = ({ label, ai, children }) => (
  <div className="form-group" style={{ marginBottom: '1rem' }}>
    <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
      {label}
      {ai && <span className="ai-badge">AI Suggested</span>}
    </label>
    {children}
  </div>
);

const baseInputStyle = { width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' };

const aiInputStyle = {
  ...baseInputStyle,
  borderColor: 'rgba(129, 140, 248, 0.4)',
  background: 'rgba(129, 140, 248, 0.02)',
  boxShadow: '0 0 10px rgba(129, 140, 248, 0.05) inset',
};

const BatchEditModal = ({ item, aiSuggestedFields: initialAiFields = [], onClose, onSave }) => {
  const [form, setForm] = useState({
    asset_name: "", asset_type: "image", description: "", created_by: "", owner: "", usage_rights: "Internal Only", geographic_restrictions: "", platform_restrictions: "", source_ownership: "", model_release_status: "Not Required", domain: "AI", use_case: "website", audience: "enterprise", funnel_stage: "awareness", campaign: "", service_line: "", geography: "", language: "", channel: "", expiry_date: "", video_duration_seconds: "", video_aspect_ratio: "16:9", video_transcript: "", keywords: "", visual_elements: "", tone: "professional",
    ...item.metadata
  });
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [aiFields, setAiFields] = useState(initialAiFields);

  const isVideoType = VIDEO_TYPES.includes(form.asset_type);
  const requiresCampaign = CAMPAIGN_REQUIRED_TYPES.includes(form.asset_type);
  const requiresServiceLine = SERVICE_LINE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresAudienceUseCase = AUDIENCE_USE_CASE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresDomain = DOMAIN_REQUIRED_TYPES.includes(form.asset_type);
  const recommendsExpiry = EXPIRY_RECOMMENDED_TYPES.includes(form.asset_type);

  // Helper: is a field AI-suggested?
  const isAi = (fieldName) => aiFields.includes(fieldName);

  // Helper: get the correct input style (with AI highlight if applicable)
  const getStyle = (fieldName, extraStyle) => {
    const base = isAi(fieldName) ? aiInputStyle : baseInputStyle;
    return extraStyle ? { ...base, ...extraStyle } : base;
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    // Remove the AI suggestion badge when user manually edits the field
    setAiFields((prev) => prev.filter((f) => f !== e.target.name));
    setError("");
  };

  const handleNext = () => {
    if (step === 0) {
      if (!form.asset_name || !form.description || !form.created_by || !form.usage_rights || !form.owner) {
        setError("Please fill in all mandatory fields.");
        return;
      }
    } else if (step === 1) {
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
    setStep(s => s + 1);
  };

  const handleBack = () => { setError(""); setStep(s => s - 1); };

  const handleSave = () => {
    onSave(item.id, form);
  };

  return (
    <div className="resolve-overlay" onClick={onClose} style={{ zIndex: 1000 }}>
      <div 
        className="resolve-modal" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '700px', width: '90%', maxHeight: '90vh', overflowY: 'auto' }}
      >
        <div className="resolve-modal-header">
          <div className="resolve-modal-title">
            <span>Edit Metadata: {item.file.name}</span>
          </div>
          <button className="resolve-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="resolve-modal-body" style={{ padding: '1.5rem' }}>
          <div className="wizard-steps" style={{ marginBottom: '2rem' }}>
            {STEPS.map((label, i) => (
              <div key={label} className={`wizard-step ${i === step ? "wizard-step--active" : i < step ? "wizard-step--done" : ""}`}>
                <div className="wizard-step-num">{i < step ? <CheckCircle size={14} /> : i + 1}</div>
                <span className="wizard-step-label">{label}</span>
              </div>
            ))}
          </div>

          {/* ─────────── STEP 0: MANDATORY (AI Recommended) ─────────── */}
          {step === 0 && (
            <div className="wizard-fields">
              <h2 className="wizard-section-title" style={{ fontSize: '1rem', marginBottom: '1.25rem' }}>
                Mandatory Information
                {aiFields.some((f) => ["asset_name", "asset_type", "description", "created_by", "owner", "usage_rights"].includes(f)) && (
                  <span className="ai-badge ai-badge--step">AI Recommended</span>
                )}
              </h2>

              <Field label="Asset Name *" ai={isAi("asset_name")}>
                <input name="asset_name" value={form.asset_name} onChange={handleChange}
                  placeholder="e.g. Marketing Banner"
                  style={getStyle("asset_name")} />
              </Field>
              <Field label="Asset Type *" ai={isAi("asset_type")}>
                <select name="asset_type" value={form.asset_type} onChange={handleChange}
                  style={getStyle("asset_type")}>
                  {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              {isVideoType && (
                <div className="video-type-notice" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'var(--surface-hover)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <Film size={14} /> Video-specific fields will be available in the Business step.
                </div>
              )}
              <Field label="Description *" ai={isAi("description")}>
                <textarea name="description" value={form.description} onChange={handleChange} rows={3}
                  style={getStyle("description")} />
              </Field>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <Field label="Created By *" ai={isAi("created_by")}>
                    <input name="created_by" value={form.created_by} onChange={handleChange}
                      style={getStyle("created_by")} />
                  </Field>
                </div>
                <div style={{ flex: 1 }}>
                  <Field label="Owner *" ai={isAi("owner")}>
                    <input name="owner" value={form.owner} onChange={handleChange}
                      style={getStyle("owner")} />
                  </Field>
                </div>
              </div>
              <Field label="Usage Rights *" ai={isAi("usage_rights")}>
                <select name="usage_rights" value={form.usage_rights} onChange={handleChange}
                  style={getStyle("usage_rights")}>
                  {USAGE_RIGHTS.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
                </select>
              </Field>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Geographic Restrictions"><input name="geographic_restrictions" value={form.geographic_restrictions} onChange={handleChange} placeholder="e.g. US, CA, UK" style={baseInputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Platform Restrictions"><input name="platform_restrictions" value={form.platform_restrictions} onChange={handleChange} placeholder="e.g. facebook, tiktok" style={baseInputStyle} /></Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Source Ownership"><input name="source_ownership" value={form.source_ownership} onChange={handleChange} placeholder="e.g. Internal, Stock Agency" style={baseInputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Model Release Status">
                  <select name="model_release_status" value={form.model_release_status} onChange={handleChange} style={baseInputStyle}>
                    <option value="Not Required">Not Required</option><option value="Pending">Pending</option><option value="Approved">Approved</option>
                  </select>
                </Field></div>
              </div>
            </div>
          )}

          {/* ─────────── STEP 1: BUSINESS (AI Recommended) ─────────── */}
          {step === 1 && (
            <div className="wizard-fields">
              <h2 className="wizard-section-title" style={{ fontSize: '1rem', marginBottom: '1.25rem' }}>
                Business Metadata
                {aiFields.some((f) => ["domain", "use_case", "audience", "funnel_stage"].includes(f)) && (
                  <span className="ai-badge ai-badge--step">AI Recommended</span>
                )}
                <span className="adaptive-badge" style={{ fontSize: '0.75rem', marginLeft: '0.75rem' }}>
                  Adapted for: <strong>{form.asset_type}</strong>
                </span>
              </h2>

              {(requiresCampaign || requiresServiceLine || requiresAudienceUseCase || requiresDomain) && (
                <div className="adaptive-rules-notice" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'var(--surface-hover)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <AlertCircle size={14} />
                  <span><strong>{form.asset_type}</strong> requires: {requiresDomain && "Domain "} {requiresCampaign && "Campaign or Service Line "} {requiresServiceLine && "+ Service Line "} {requiresAudienceUseCase && "Audience + Use Case"}</span>
                </div>
              )}
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <Field label={`Domain${requiresDomain ? " *" : ""}`} ai={isAi("domain")}>
                    <select name="domain" value={form.domain} onChange={handleChange}
                      style={getStyle("domain")}>
                      {DOMAIN_TYPES.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </Field>
                </div>
                <div style={{ flex: 1 }}>
                  <Field label={`Use Case${requiresAudienceUseCase ? " *" : ""}`} ai={isAi("use_case")}>
                    <select name="use_case" value={form.use_case} onChange={handleChange}
                      style={getStyle("use_case")}>
                      {USE_CASES.map(u => <option key={u} value={u}>{u}</option>)}
                    </select>
                  </Field>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <Field label={`Audience${requiresAudienceUseCase ? " *" : ""}`} ai={isAi("audience")}>
                    <select name="audience" value={form.audience} onChange={handleChange}
                      style={getStyle("audience")}>
                      {AUDIENCE_TYPES.map(a => <option key={a} value={a}>{a}</option>)}
                    </select>
                  </Field>
                </div>
                <div style={{ flex: 1 }}>
                  <Field label="Funnel Stage" ai={isAi("funnel_stage")}>
                    <select name="funnel_stage" value={form.funnel_stage} onChange={handleChange}
                      style={getStyle("funnel_stage")}>
                      {FUNNEL_STAGES.map(f => <option key={f} value={f}>{f}</option>)}
                    </select>
                  </Field>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label={`Campaign${requiresCampaign ? " *" : ""}`}>
                  <input name="campaign" value={form.campaign} onChange={handleChange} placeholder="e.g. Summer 2026 Campaign" style={getStyle("campaign", { borderColor: requiresCampaign && !form.campaign ? 'var(--primary)' : 'var(--border)' })} />
                </Field></div>
                <div style={{ flex: 1 }}><Field label={`Service Line${requiresServiceLine ? " *" : ""}`}>
                  <input name="service_line" value={form.service_line} onChange={handleChange} placeholder="e.g. Enterprise Sales" style={getStyle("service_line", { borderColor: requiresServiceLine && !form.service_line ? 'var(--primary)' : 'var(--border)' })} />
                </Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Geography"><input name="geography" value={form.geography} onChange={handleChange} placeholder="e.g. North America" style={baseInputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Language"><input name="language" value={form.language} onChange={handleChange} placeholder="e.g. English" style={baseInputStyle} /></Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Channel"><input name="channel" value={form.channel} onChange={handleChange} placeholder="e.g. LinkedIn, Email" style={baseInputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label={`Expiry Date${recommendsExpiry ? " (recommended)" : ""}`}>
                  <input type="date" name="expiry_date" value={form.expiry_date} onChange={handleChange} style={getStyle("expiry_date", { borderColor: recommendsExpiry && !form.expiry_date ? 'var(--info)' : 'var(--border)' })} />
                </Field></div>
              </div>

              {isVideoType && (
                <div className="video-fields-section" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontWeight: 'bold' }}><Film size={16} /> Video Details</div>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1 }}><Field label="Duration (seconds)"><input type="number" name="video_duration_seconds" value={form.video_duration_seconds} onChange={handleChange} min="0" placeholder="e.g. 90" style={baseInputStyle} /></Field></div>
                    <div style={{ flex: 1 }}><Field label="Aspect Ratio">
                      <select name="video_aspect_ratio" value={form.video_aspect_ratio} onChange={handleChange} style={baseInputStyle}>{ASPECT_RATIOS.map(r => <option key={r} value={r}>{r}</option>)}</select>
                    </Field></div>
                  </div>
                  <Field label="Transcript / Captions (optional)">
                    <textarea name="video_transcript" value={form.video_transcript} onChange={handleChange} rows={3} placeholder="Paste video transcript or captions here…" style={baseInputStyle} />
                  </Field>
                </div>
              )}
            </div>
          )}

          {/* ─────────── STEP 2: CONTENT (AI Recommended) ─────────── */}
          {step === 2 && (
            <div className="wizard-fields">
              <h2 className="wizard-section-title" style={{ fontSize: '1rem', marginBottom: '1.25rem' }}>
                Content Metadata
                {aiFields.some((f) => ["keywords", "tone"].includes(f)) && (
                  <span className="ai-badge ai-badge--step">AI Recommended</span>
                )}
              </h2>

              <Field label="Keywords" ai={isAi("keywords")}>
                <input name="keywords" value={form.keywords} onChange={handleChange}
                  placeholder="marketing, brand, summer — comma separated"
                  style={getStyle("keywords")} />
              </Field>
              <Field label="Visual Elements">
                <input name="visual_elements" value={form.visual_elements} onChange={handleChange}
                  placeholder="logo, person, outdoor — comma separated" style={baseInputStyle} />
              </Field>
              <Field label="Tone" ai={isAi("tone")}>
                <select name="tone" value={form.tone} onChange={handleChange}
                  style={getStyle("tone")}>
                  {TONE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
            </div>
          )}

          {error && <div className="auth-error" style={{ color: 'var(--danger)', fontSize: '0.9rem', marginTop: '1rem' }}>{error}</div>}
        </div>

        <div className="resolve-modal-footer" style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 1.5rem', borderTop: '1px solid var(--border)' }}>
          <div>
            {step > 0 && <button className="resolve-btn-cancel" onClick={handleBack} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><ArrowLeft size={16} /> Back</button>}
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="resolve-btn-cancel" onClick={onClose}>Cancel</button>
            {step < STEPS.length - 1 ? (
              <button className="resolve-btn-submit" onClick={handleNext} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>Next <ArrowRight size={16} /></button>
            ) : (
              <button className="resolve-btn-submit" onClick={handleSave} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle size={16} /> Save Metadata</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchEditModal;
