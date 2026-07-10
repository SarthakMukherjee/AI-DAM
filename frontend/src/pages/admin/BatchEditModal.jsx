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

const Field = ({ label, required, children }) => (
  <div className="form-group" style={{ marginBottom: '1rem' }}>
    <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
      {label}
    </label>
    {children}
  </div>
);

const inputStyle = { width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' };

const BatchEditModal = ({ item, onClose, onSave }) => {
  const [form, setForm] = useState({
    asset_name: "", asset_type: "image", description: "", created_by: "", owner: "", usage_rights: "Internal Only", geographic_restrictions: "", platform_restrictions: "", source_ownership: "", model_release_status: "Not Required", domain: "AI", use_case: "website", audience: "enterprise", funnel_stage: "awareness", campaign: "", service_line: "", geography: "", language: "", channel: "", expiry_date: "", video_duration_seconds: "", video_aspect_ratio: "16:9", video_transcript: "", keywords: "", visual_elements: "", tone: "professional",
    ...item.metadata
  });
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");

  const isVideoType = VIDEO_TYPES.includes(form.asset_type);
  const requiresCampaign = CAMPAIGN_REQUIRED_TYPES.includes(form.asset_type);
  const requiresServiceLine = SERVICE_LINE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresAudienceUseCase = AUDIENCE_USE_CASE_REQUIRED_TYPES.includes(form.asset_type);
  const requiresDomain = DOMAIN_REQUIRED_TYPES.includes(form.asset_type);
  const recommendsExpiry = EXPIRY_RECOMMENDED_TYPES.includes(form.asset_type);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
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

          {step === 0 && (
            <div className="wizard-fields">
              <Field label="Asset Name *">
                <input name="asset_name" value={form.asset_name} onChange={handleChange} style={inputStyle} />
              </Field>
              <Field label="Asset Type *">
                <select name="asset_type" value={form.asset_type} onChange={handleChange} style={inputStyle}>
                  {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              {isVideoType && (
                <div className="video-type-notice" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'var(--surface-hover)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <Film size={14} /> Video-specific fields will be available in the Business step.
                </div>
              )}
              <Field label="Description *">
                <textarea name="description" value={form.description} onChange={handleChange} rows={3} style={inputStyle} />
              </Field>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Created By *"><input name="created_by" value={form.created_by} onChange={handleChange} style={inputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Owner *"><input name="owner" value={form.owner} onChange={handleChange} style={inputStyle} /></Field></div>
              </div>
              <Field label="Usage Rights *">
                <select name="usage_rights" value={form.usage_rights} onChange={handleChange} style={inputStyle}>
                  {USAGE_RIGHTS.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
                </select>
              </Field>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Geographic Restrictions"><input name="geographic_restrictions" value={form.geographic_restrictions} onChange={handleChange} style={inputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Platform Restrictions"><input name="platform_restrictions" value={form.platform_restrictions} onChange={handleChange} style={inputStyle} /></Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Source Ownership"><input name="source_ownership" value={form.source_ownership} onChange={handleChange} style={inputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Model Release Status">
                  <select name="model_release_status" value={form.model_release_status} onChange={handleChange} style={inputStyle}>
                    <option value="Not Required">Not Required</option><option value="Pending">Pending</option><option value="Approved">Approved</option>
                  </select>
                </Field></div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="wizard-fields">
              {(requiresCampaign || requiresServiceLine || requiresAudienceUseCase || requiresDomain) && (
                <div className="adaptive-rules-notice" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'var(--surface-hover)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <AlertCircle size={14} />
                  <span><strong>{form.asset_type}</strong> requires: {requiresDomain && "Domain "} {requiresCampaign && "Campaign or Service Line "} {requiresServiceLine && "+ Service Line "} {requiresAudienceUseCase && "Audience + Use Case"}</span>
                </div>
              )}
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label={`Domain${requiresDomain ? " *" : ""}`}>
                  <select name="domain" value={form.domain} onChange={handleChange} style={inputStyle}>{DOMAIN_TYPES.map(d => <option key={d} value={d}>{d}</option>)}</select>
                </Field></div>
                <div style={{ flex: 1 }}><Field label={`Use Case${requiresAudienceUseCase ? " *" : ""}`}>
                  <select name="use_case" value={form.use_case} onChange={handleChange} style={inputStyle}>{USE_CASES.map(u => <option key={u} value={u}>{u}</option>)}</select>
                </Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label={`Audience${requiresAudienceUseCase ? " *" : ""}`}>
                  <select name="audience" value={form.audience} onChange={handleChange} style={inputStyle}>{AUDIENCE_TYPES.map(a => <option key={a} value={a}>{a}</option>)}</select>
                </Field></div>
                <div style={{ flex: 1 }}><Field label="Funnel Stage">
                  <select name="funnel_stage" value={form.funnel_stage} onChange={handleChange} style={inputStyle}>{FUNNEL_STAGES.map(f => <option key={f} value={f}>{f}</option>)}</select>
                </Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label={`Campaign${requiresCampaign ? " *" : ""}`}>
                  <input name="campaign" value={form.campaign} onChange={handleChange} style={{...inputStyle, borderColor: requiresCampaign && !form.campaign ? 'var(--primary)' : 'var(--border)'}} />
                </Field></div>
                <div style={{ flex: 1 }}><Field label={`Service Line${requiresServiceLine ? " *" : ""}`}>
                  <input name="service_line" value={form.service_line} onChange={handleChange} style={{...inputStyle, borderColor: requiresServiceLine && !form.service_line ? 'var(--primary)' : 'var(--border)'}} />
                </Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Geography"><input name="geography" value={form.geography} onChange={handleChange} style={inputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Language"><input name="language" value={form.language} onChange={handleChange} style={inputStyle} /></Field></div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}><Field label="Channel"><input name="channel" value={form.channel} onChange={handleChange} style={inputStyle} /></Field></div>
                <div style={{ flex: 1 }}><Field label={`Expiry Date${recommendsExpiry ? " (recommended)" : ""}`}>
                  <input type="date" name="expiry_date" value={form.expiry_date} onChange={handleChange} style={{...inputStyle, borderColor: recommendsExpiry && !form.expiry_date ? 'var(--info)' : 'var(--border)'}} />
                </Field></div>
              </div>

              {isVideoType && (
                <div className="video-fields-section" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontWeight: 'bold' }}><Film size={16} /> Video Details</div>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1 }}><Field label="Duration (seconds)"><input type="number" name="video_duration_seconds" value={form.video_duration_seconds} onChange={handleChange} min="0" style={inputStyle} /></Field></div>
                    <div style={{ flex: 1 }}><Field label="Aspect Ratio">
                      <select name="video_aspect_ratio" value={form.video_aspect_ratio} onChange={handleChange} style={inputStyle}>{ASPECT_RATIOS.map(r => <option key={r} value={r}>{r}</option>)}</select>
                    </Field></div>
                  </div>
                  <Field label="Transcript / Captions (optional)">
                    <textarea name="video_transcript" value={form.video_transcript} onChange={handleChange} rows={3} style={inputStyle} />
                  </Field>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="wizard-fields">
              <Field label="Keywords"><input name="keywords" value={form.keywords} onChange={handleChange} placeholder="comma separated" style={inputStyle} /></Field>
              <Field label="Visual Elements"><input name="visual_elements" value={form.visual_elements} onChange={handleChange} placeholder="comma separated" style={inputStyle} /></Field>
              <Field label="Tone">
                <select name="tone" value={form.tone} onChange={handleChange} style={inputStyle}>{TONE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}</select>
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
