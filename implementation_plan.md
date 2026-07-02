# AI-DAM Feature Gap Analysis & Implementation Plan

## What This System Does Now

A full-stack Digital Asset Management (DAM) platform built with FastAPI + PostgreSQL + ChromaDB (backend) and React + Vite (frontend), deployed on Cloudinary for storage.

---

## ✅ BUILT — What Already Exists

### Backend
| Area | What's Built |
|---|---|
| **Auth** | JWT-based login/register, role-based access: `super_admin`, `admin`, `reviewer`, `user` |
| **Asset Upload** | Multi-step upload with versioning (`parent_id`), file hash generation, cloud (Cloudinary) storage |
| **Duplicate Detection** | File hash (`SHA256`) exact-match check at upload time — blocks re-upload |
| **Versioning** | `version`, `parent_id`, `root_asset_id`, `is_latest` fields on the Asset model |
| **Preview Generation** | Image thumbnails, PDF page-1 preview, video frame thumbnail |
| **Approval Workflow** | Status lifecycle: `draft → approved / rejected`; reviewer approves/rejects; admin gets notified on rejection |
| **AI Auto-tagging** | LLM (Groq/Llama) generates tags for images, PDFs, videos post-upload |
| **AI Metadata Suggestion** | `/assets/analyze` endpoint: pre-fill `asset_name`, `asset_type`, `description`, `owner`, `usage_rights` before upload |
| **OCR** | Text extraction from images and PDFs |
| **Semantic Search** | ChromaDB vector store + embedding pipeline — natural language search |
| **Hybrid Search** | Keyword (PostgreSQL) + Semantic (ChromaDB) search merged with `0.6/0.4` scoring |
| **Analytics (basic)** | `AssetUsage` model tracks download/preview actions; most-used assets endpoint |
| **Notifications** | Admin receives rejection alerts; mark-read / mark-all-read |
| **User Management** | Super admin: list users, promote/demote roles, deactivate/reactivate |
| **Archive flag** | `is_archived` boolean on Asset model |
| **Metadata Schema** | Structured: `mandatory`, `business`, `content`, `ai_enrichment` sections with Pydantic validation |

### Frontend
| Area | What's Built |
|---|---|
| **Smart Upload Wizard** | 4-step wizard (Upload → Mandatory → Business → Content) with AI field pre-fill and "AI Suggested" badge |
| **Asset Browser** | Grid view with Hybrid + Semantic search toggle |
| **Asset Card + Modal** | Preview, metadata display, download |
| **Review Queue** | Reviewer approve/reject with reason |
| **Admin Dashboard** | Asset list, delete |
| **Super Admin Dashboard** | User management, role changes |
| **Analytics Page** | Most-used assets |
| **Notification Bell** | Live unread count, mark-read |

---

## ❌ NOT BUILT — Gaps Against Your 16 Requirements

---

### 1. Asset Model & Classes — PARTIAL
**What's missing:**
- `AssetTypes` enum only has: `image`, `video`, `pdf`, `document` — no specific classes like `banner`, `brochure`, `case study`, `testimonial`, `logo`, `social creative`, `pitch deck`, `brand guideline`, `campaign file`
- No per-asset-class metadata rules (e.g., video needs `duration`, `transcript`; brochure needs `campaign`, `service line`)
- No per-asset-class preview logic differences
- No concept of "website-safe" flag, `alt_text`, or brand-guideline alignment flag

---

### 2. Metadata & Taxonomy — PARTIAL
**What's missing:**
- `service_line` field — not present
- `geography` / `region` field — not present
- `campaign` field — not present
- `language` field — not present
- `approval_status` as a tracked field (exists as `status` but not surfaced richly)
- `expiry_date` / `expiry_reminder` — not present
- `channel` field (web, social, email, print) — not present
- Usage rights is a free-text field — no controlled vocabulary / dropdown
- `created_by` and `owner` are free-text — should link to user records
- `AssetTypes` enum needs expansion to match real asset classes

---

### 3. AI Retrieval — PARTIAL
**What's missing:**
- Near-duplicate detection (perceptual hash / visual similarity) — only exact file-hash deduplication exists
- AI-generated summary not stored separately (extracted text exists but no clean summary field)
- No "missing metadata completeness score" flag per asset
- AI enrichment runs but results stored inside `asset_metadata` JSONB — not queryable as individual columns

---

### 4. Search Quality — PARTIAL
**What's missing:**
- No faceted filtering UI (filter by `domain`, `status`, `asset_type`, `geography`, `campaign`, `language` simultaneously)
- Search results don't show status badges (approved, latest, archived, restricted) prominently
- No "search within specific metadata field" (e.g., search only in `campaign`)
- No saved search or recent search
- No search result ranking explanation shown to user

---

### 5. Version Control — PARTIAL
**What's built:** `version`, `parent_id`, `root_asset_id`, `is_latest` exist in data model.

**What's missing:**
- No version history UI — can't browse previous versions of an asset
- No changelog per version (what changed, who changed it)
- No "retire/replace" action — retired versions just have `is_latest = False` but no explicit retire status
- No master asset view that shows full version tree
- `updated_at` timestamp missing from Asset model (only `created_at`)

---

### 6. Approval Workflow — PARTIAL
**What's built:** `draft → approved / rejected` transition exists.

**What's missing:**
- No `pending_review`, `published`, `restricted` statuses in actual workflow (enum defines them but no routes handle them)
- No `published` status distinct from `approved`
- No `restricted` status with access control logic
- No role-based approval scope (who can approve which asset types / domains)
- No "submit for review" action separate from upload (assets go to `draft` automatically — no explicit submission)
- Rejection doesn't carry structured feedback fields (only free-text `reason`)

---

### 7. Permissions & Access Logic — PARTIAL
**What's built:** 4 roles — `super_admin`, `admin`, `reviewer`, `user`.

**What's missing:**
- `marketing_manager`, `designer`, `content_lead`, `sales_user`, `external_partner`, `website_team` roles — not defined
- No domain/business-unit scoped access (user X can only see assets tagged with `domain = Healthcare`)
- No "upload but not approve" role distinction (currently admin = upload + approve)
- No external partner access tier (time-limited, restricted asset subset)
- No per-asset access restriction (mark an asset as viewable by specific roles only)

---

### 8. Asset Previews & Usability — PARTIAL
**What's built:** Thumbnails, preview modal, basic metadata display.

**What's missing:**
- File dimensions not stored or displayed for images
- Asset detail page (not just modal) with full metadata, version history, usage stats
- Bulk download
- Rich metadata display — tags, AI enrichment, completeness score all visible at-a-glance
- Status badges visible directly on asset cards (not just inside modal)
- "Missing metadata" visual warning on cards

---

### 9. Website & Marketing Usage Context — NOT BUILT
**What's missing:**
- "Where is this asset used?" — no CMS or page linkage
- `website_safe` flag
- `public_use_approved` flag distinct from general `approved`
- Compressed / resized web-ready output versions
- `alt_text` field for web accessibility
- `brand_guideline_aligned` flag
- Campaign attribution with `campaign_id` / `campaign_name`

---

### 10. Smart Upload Flow — PARTIAL
**What's built:** AI pre-fills mandatory fields; 4-step wizard exists.

**What's missing:**
- Upload flow does NOT adapt per asset type (video should ask `duration`, `transcript`, `thumbnail`; brochure should ask `campaign`, `service_line`)
- Drag-and-drop not implemented (click-only)
- Batch upload (multiple files at once) not supported
- Geography/region field not collected at upload
- Language field not collected at upload

---

### 11. Duplicate Prevention — PARTIAL
**What's built:** Exact SHA256 hash match blocks re-upload.

**What's missing:**
- Perceptual hash (pHash / dHash) for near-duplicate image detection
- Visual similarity search ("find visually similar assets")
- Duplicate candidate flagging in UI
- Recommend merge / replace workflow for duplicates

---

### 12. Archive & Expiry Logic — PARTIAL
**What's built:** `is_archived` boolean exists.

**What's missing:**
- No archive action in UI or API route (no `PATCH /assets/{id}/archive` endpoint)
- `expiry_date` field not in model
- No expiry reminder / alert system
- Archived assets still appear in search results (no `is_archived` filter in search)
- No "archive reason" field

---

### 13. Audit Trail — PARTIAL
**What's built:** `AssetUsage` tracks download/preview counts.

**What's missing:**
- No audit log model (who uploaded, who changed metadata, who approved, who rejected, who deleted)
- No per-action user attribution in `AssetUsage` (only asset_id + action — no user_id)
- No metadata edit history
- No "last downloaded by" tracking
- No searchable audit log UI

---

### 14. UI Trust & Control — PARTIAL
**What's built:** Basic status display, AI Suggested badge, empty states.

**What's missing:**
- `approved`, `latest`, `restricted`, `archived`, `AI-tagged`, `missing metadata`, `duplicate candidate` labels not consistently visible on asset cards
- No onboarding flow / guided tour for new users
- No metadata completeness indicator per asset
- No "this asset has missing required fields" banner

---

### 15. Reporting & Intelligence — MINIMAL
**What's built:** Most-used assets analytics endpoint.

**What's missing:**
- Unused assets report (assets with zero downloads)
- Duplicate-heavy category report
- Missing metadata completeness report
- Asset request tracking by business unit
- Time-to-approval analytics
- Content type coverage gap report (frequently searched but poorly served)
- Downloadable reports (CSV export)

---

### 16. Integrations — NOT BUILT
**What's missing:**
- No CMS connector (WordPress, Contentful, etc.)
- No design tool integration (Figma, Canva)
- No API key / OAuth scoping for external systems
- No webhook system for asset state changes
- Data model currently not integration-ready (IDs are UUIDs — good; but no external_id mapping field)
- No public asset delivery API (headless DAM endpoint)

---

## Priority Build Order (Recommended)

### Phase 1 — Foundation Fixes (High Impact, Low Risk)
1. Expand `AssetTypes` enum with real asset classes (banner, brochure, case study, logo, etc.)
2. Add missing metadata fields to schema: `service_line`, `geography`, `language`, `channel`, `campaign`, `expiry_date`
3. Add `updated_at`, `archived_at` to Asset model; add `PATCH /assets/{id}/archive` route
4. Add `user_id` to `AssetUsage` for user attribution
5. Add `pending_review`, `published`, `restricted` to actual workflow routes (not just enum)

### Phase 2 — Search & Discovery Upgrade (Core Value)
6. Faceted filter UI in Asset Browser (status, type, domain, geography, language, campaign)
7. Status badges visible on asset cards
8. Near-duplicate detection using perceptual hashing (pHash)
9. Missing metadata completeness score per asset

### Phase 3 — Version Control & Workflow
10. Version history UI — browse full version tree per asset
11. Changelog per version (what changed, who changed it, `updated_at`)
12. Archive & expiry logic — UI action + expiry date field + reminder system
13. "Submit for review" explicit action (currently auto-submitted on upload)

### Phase 4 — Role & Permission Expansion
14. New roles: `marketing_manager`, `designer`, `content_lead`, `sales_user`, `external_partner`
15. Domain-scoped access (user sees only assets of their assigned domain)
16. Per-asset access restriction flag

### Phase 5 — Audit Trail & Reporting
17. Full audit log model (`AuditLog`) with user, action, field, old_value, new_value, timestamp
18. Audit log UI
19. Unused assets, missing metadata, time-to-approval, content gap reports
20. CSV export for all reports

### Phase 6 — Smart Upload & Asset-Type Awareness
21. Adaptive upload wizard (different fields per asset class)
22. Drag-and-drop support
23. Batch upload (multiple files)
24. Video-specific fields: `duration`, `transcript`, `thumbnail_override`

### Phase 7 — Website & Marketing Context
25. `website_safe`, `public_use_approved`, `brand_aligned`, `alt_text` fields
26. Asset usage context ("used on page X")
27. Web-ready compressed output generation

### Phase 8 — Integration Layer
28. Webhook system for asset state changes
29. External API key system for headless access
30. `external_id` mapping for CMS/third-party sync

---

## Open Questions

> [!IMPORTANT]
> **Q1: Asset class definitions** — Should the expanded asset types (banner, brochure, pitch deck, etc.) be a flat enum, or should there be a parent class (e.g., `Marketing > Banner`, `Marketing > Brochure`)?

> [!IMPORTANT]
> **Q2: Workflow depth** — Should `published` be a distinct status from `approved`, or is `approved = published` for now?

> [!IMPORTANT]
> **Q3: Role expansion priority** — Which new roles are needed first? `marketing_manager` and `designer` or `external_partner`?

> [!IMPORTANT]
> **Q4: Near-duplicate threshold** — For perceptual hash similarity, what visual similarity % should trigger a "duplicate candidate" warning?

> [!IMPORTANT]
> **Q5: Phase 1 start** — Should we start with Phase 1 (metadata + model fixes) immediately, or is there a specific feature from the list above that is most urgent?
