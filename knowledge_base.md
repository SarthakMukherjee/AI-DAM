# AI-DAM LLM Knowledge Base & Feature Building Blueprint

> **Purpose:** This document is engineered specifically to be fed into an LLM (Claude, GPT-4, Gemini, etc.) at the beginning of a coding session. It gives the LLM complete architectural rules, strict coding boundaries, standard operating procedures, and exact, self-contained technical blueprints for building any remaining feature **one at a time** without breaking existing functionality.
> **Current Completion Status:** ~86% Complete (45 of 52 core items built). Phases 1, 2, 3, 4, 6 and 7 are 100% complete. Phase 5 is partially built. Phase 8 is unbuilt.

---

## SECTION 1: SYSTEM IDENTITY & STRICT LLM RULES OF ENGAGEMENT

When operating on the AI-DAM codebase, you **MUST strictly abide by the following architectural boundaries**:

### 1. Actual Tech Stack (Do NOT rely on `techstack.md`)
* **Frontend:** React 18 + Vite + JavaScript (JSX). **NOT Next.js.**
* **Styling:** Vanilla CSS scoped per component in `frontend/src/styles/`. **Do NOT install or use Tailwind CSS, Styled Components, or CSS Modules.** Use CSS variables defined in root styles.
* **Backend API:** Python 3.10+ with FastAPI.
* **Database:** PostgreSQL accessed via SQLAlchemy (Synchronous ORM).
* **Migrations:** **NO ALEMBIC.** Schema migrations are handled via self-healing DDL in `backend/app/db/migrate.py`.
* **Vector Store:** ChromaDB (Local/Docker volume). **NOT pgvector.**
* **File Storage:** Local Filesystem (`STORAGE_BACKEND="local"`, where `storage_path` stores local file paths in `storage/` directory; architecture built ready for future transition to AWS S3 bucket). All file types (images, videos, documents, archives, audio, etc.) are permitted and supported.
* **AI & Embeddings:** Groq API (Llama 3) for auto-tagging/summaries; Sentence Transformers (`all-MiniLM-L6-v2`) locally for vector embeddings; Tesseract / PyMuPDF for OCR.
* **Auth & Security:** JWT Bearer tokens with HTTP-only cookies support; rate limiting via SlowAPI.

### 2. Forbidden Actions
1. **Never introduce Alembic** or generate migration scripts. Always edit `backend/app/db/migrate.py` and the SQLAlchemy model.
2. **Never convert JSX to TypeScript** unless specifically instructed by the user. Keep files as `.jsx`.
3. **Never add Celery, Redis, or heavy asynchronous workers** for existing AI pipelines unless instructed. Currently, all upload AI pipelines run synchronously.
4. **Never modify existing metadata enums or core schemas** in a breaking way that invalidates existing stored JSONB records.

---

## SECTION 2: STANDARD OPERATING PROCEDURE (SOP) FOR BUILDING ONE FEATURE

Whenever the user prompts: *"Here is knowledge_base.md. Build Feature [X]"*, follow this exact 5-step protocol:

```
[Step 1: DB Schema & Models] -> Update migrate.py + SQLAlchemy Model + Pydantic Schemas
       ↓
[Step 2: Backend Logic]      -> Update/Create Services, AI logic, or Helpers
       ↓
[Step 3: API Routes]         -> Create/Update Router + Role Gate Dependencies + Register in main.py
       ↓
[Step 4: Frontend UI]        -> Add API client call + Update React Component + Write Vanilla CSS
       ↓
[Step 5: Verification]       -> Review DB/Chroma synchronization & Role Access Guards
```

### Step 1: Database & Schema Synchronization
* If adding a column to existing tables (`assets`, `users`), add a tuple `("col_name", "SQL_TYPE")` to `_ASSET_COLUMNS` or `_USER_COLUMNS` in `backend/app/db/migrate.py`.
* Update the SQLAlchemy model in `backend/app/models/`.
* Update or create request/response Pydantic schemas in `backend/app/schemas/`.

### Step 2: Backend Service & Business Logic
* Place core domain logic inside `backend/app/services/` or utility helpers in `backend/app/utils/`.
* If modifying asset attributes or metadata that affects search, ensure ChromaDB vector store (`backend/app/ai/vectorstore/`) is updated accordingly.

### Step 3: API Route & Security Gates
* Place routes inside `backend/app/api/routes/`.
* Secure all non-public endpoints using `Depends(get_current_user)`.
* If action requires specific roles, enforce check via `check_restricted_access()` or role verification functions in `backend/app/api/dependencies/auth_dependency.py`.

### Step 4: Frontend Components & Styling
* Keep API fetch calls cleanly abstracted or inside component lifecycle functions (`useEffect` / event handlers).
* Place styling in `frontend/src/styles/<ComponentName>.css` and import it into the JSX file. Keep UI rich, clean, modern, and dark-mode friendly.

---

## SECTION 3: DATABASE MIGRATION REFERENCE

When your feature requires adding columns:
1. Open `backend/app/db/migrate.py`.
2. Locate the appropriate column list:
   ```python
   _ASSET_COLUMNS: list[tuple[str, str]] = [
       # Add your column here, e.g.:
       ("website_safe", "BOOLEAN DEFAULT FALSE"),
   ]
   ```
3. Open `backend/app/models/asset/asset_model.py` (or corresponding model) and declare the column:
   ```python
   website_safe = Column(Boolean, default=False)
   ```
4. When FastAPI restarts, `upgrade_db_schema()` automatically executes:
   `ALTER TABLE assets ADD COLUMN IF NOT EXISTS website_safe BOOLEAN DEFAULT FALSE;`

If your feature requires a **new table** (e.g., `audit_logs` or `asset_webhooks`):
1. Create a new model file `backend/app/models/<category>/<table_name>_model.py`.
2. Inherit from `Base` (`from app.db.session.database import Base`).
3. Import the new model inside `backend/app/main.py` before calling `Base.metadata.create_all(bind=engine)`.

---

## SECTION 4: MASTER FEATURE BLUEPRINT CATALOG

Features marked **✅ DONE** are fully implemented and should NOT be rebuilt. Only add to or fix them if the user reports a specific bug.

Choose ONE unbuilt feature from below when instructed by the user and execute all specified tasks.

---

### ✅ DONE — Phase 6: Smart Upload & Asset-Type Awareness

> Built: 2026-07-06

**6.1 Adaptive Upload Wizard** 
`UploadAsset.jsx` Step 2 (Business) now dynamically shows required fields by asset_type:
- `video`, `social_creative` → require **campaign** OR **service_line**
- `brochure`, `campaign_file` → require both **campaign** AND **service_line**
- `pitch_deck` → require **audience** + **use_case**
- `logo`, `brand_guideline` → require **domain**
- `brochure`, `campaign_file`, `social_creative` → expiry_date field shown with `field-recommended-highlight`
- Validation happens in `handleNext()` when leaving step 2. Amber banner shown at top of Business step.
- **AI Integration**: The `suggest_metadata` prompt in `auto_tagging_service.py` was expanded to infer 6 additional fields (domain, use_case, audience, funnel_stage, tone, keywords) from the file content. These map to the form state and show an `ai-badge` and indigo glow in the Business and Content steps when populated.

**6.2 Drag-and-Drop Upload** 
Drop zone in `UploadAsset.jsx` step 0 uses `onDragOver`, `onDragLeave`, `onDrop` handlers on the `<div>` with `ref={dropRef}`. `isDragOver` state drives `.upload-dropzone--drag-over` CSS class (indigo glow + `scale(1.01)`). Works in both single and batch modes.

**6.3 Batch Upload** 
Batch Mode toggle in header renders a separate `batch-panel` UI (not the wizard). Multi-file support via `multiple` attribute on hidden `<input>` and drag-and-drop. Sequential processing queue:
1. Status: `queued` → `analyzing` (calls `POST /assets/analyze`) → `uploading` (calls `POST /assets/upload`) → `done` or `error`
2. Per-file progress bar via `onUploadProgress` axios callback
3. Files removed from queue individually with trash button (only while queued)
4. Summary banner at end showing X uploaded, Y failed

**6.4 Video-Specific Fields** 
- DB: `video_duration_seconds INTEGER`, `video_transcript TEXT`, `video_aspect_ratio VARCHAR(20)` added to `migrate.py` (`_ASSET_COLUMNS`) and `asset_model.py`
- Upload route (`POST /assets/upload`) accepts these as optional `Form(None)` fields and saves them to the asset row after creation
- UI: `video-fields-section` div appears in Business step only when `asset_type` is `video` or `social_creative`. Fields: duration (number), aspect ratio (select: 16:9/9:16/1:1/4:3/3:4/21:9), transcript (textarea)
- Frontend sends these as additional `formData.append()` entries only when non-empty

**CSS Pattern:** All batch/drag/video/adaptive styles live in `frontend/src/styles/upload.css` at the bottom (after line 695 of original).

---

### ✅ DONE — Phase 2.4.5 + Phase 3.3

> Built: 2026-07-06

**Resolve Duplicate Modal** (`AdminDashboard.jsx`) — canonical picker, merge toggle, retire/delete action, calls `POST /assets/resolve-duplicate`.

**Expiry Alert System** — `GET /admin/assets/expiring`, `POST /admin/assets/{id}/check-expiry` in `admin_routes.py`. Expired/expiring-soon badges in `AssetCard.jsx`. Expiry banner in `AssetDetail.jsx`. "Expiring Assets" admin tab.

---

### FEATURE 2.4: Duplicate Merge / Replace Workflow

**Status:** 🟡 Backend Completed (2.4.1–2.4.4) | Frontend Pending (2.4.5)

#### Objective
Allow administrators to resolve visually similar or duplicate assets by selecting one canonical asset, optionally merging useful metadata from the duplicate, synchronizing semantic search, and retiring or permanently deleting the duplicate asset.

This workflow improves metadata quality, eliminates redundant assets, and keeps PostgreSQL and ChromaDB fully synchronized.

#### IMPLEMENTATION STATUS

**✅ Phase 2.4.1 — Duplicate Merge Service (Completed)**

Implemented:

```
backend/app/services/storage/duplicate_merge_service.py
```

Responsibilities:
* Validate canonical and duplicate asset IDs.
* Prevent self-resolution.
* Merge duplicate metadata into canonical asset.
* Merge AI enrichment metadata.
* Update SQL queryable fields.
* Execute retire or delete workflow.
* Commit database transaction.
* Return updated canonical asset.

Metadata merged:
* `content.keywords`
* `ai_enrichment.ai_tags`
* `ai_enrichment.searchable_tags`
* `ai_enrichment.detected_objects`

Queryable SQL fields updated:
* `ai_tags`
* `detected_objects`

The service removes duplicate values while preserving insertion order.

**✅ Phase 2.4.2 — API Schemas (Completed)**

Implemented in:

```
backend/app/schemas/asset_schema.py
```

Added:

```python
DuplicateResolveRequest

canonical_asset_id: str
duplicate_asset_id: str
action: Literal["retire", "delete"]
merge_metadata: bool = True
```

Added:

```python
DuplicateResolveResponse

success: bool
message: str
canonical_asset_id: str
duplicate_asset_id: str
action: str
metadata_merged: bool
```

No breaking changes were introduced to existing schemas.

**✅ Phase 2.4.3 — Backend API (Completed)**

Implemented endpoint:

```
POST /assets/resolve-duplicate
```

Location:

```
backend/app/api/routes/assets_routes.py
```

Security:
* Admin only.
* Protected through existing RBAC dependency.

Workflow:
1. Validate request.
2. Call `DuplicateMergeService`.
3. Return typed response.

Business logic remains inside the service layer to maintain architecture consistency.

**✅ Phase 2.4.4 — Chroma Synchronization (Completed)**

Added:

```
backend/app/ai/vectorstore/vector_delete_service.py
```

Purpose: Delete vectors from ChromaDB whenever duplicate assets are permanently removed.

Integrated into `DuplicateMergeService`.

Workflow:

```
Merge Metadata
        ↓
Commit PostgreSQL
        ↓
Re-index Canonical Asset
        ↓
Delete Duplicate Vector (Delete only)
        ↓
Return Updated Canonical Asset
```

Synchronization rules:

*Retire:*
* Duplicate remains in PostgreSQL.
* Duplicate vector remains.
* Existing semantic search filters prevent retired assets from appearing.

*Delete:*
* Duplicate removed from PostgreSQL.
* Duplicate vector removed from ChromaDB.
* Canonical asset re-indexed with merged metadata.

No orphan vectors remain after permanent deletion.

#### Current Backend Architecture

```
DuplicateMergeService
        │
        ├── Merge metadata
        ├── Merge AI tags
        ├── Merge detected objects
        ├── Merge searchable tags
        ├── Update SQL metadata
        │
        ▼
Commit PostgreSQL
        │
        ▼
SemanticSearchService.reindex_asset()
        │
        ▼
VectorUpsertService
        │
        ▼
ChromaDB
```

Delete workflow additionally executes:

```
VectorDeleteService
        │
        ▼
Remove duplicate vector
```

#### Pending Frontend Work

**✅ Phase 2.4.5 — Duplicate Resolution UI (Completed)**

Status: Implemented.

Location:

```
frontend/src/pages/admin/AdminDashboard.jsx
```

Current UI:

```
Resolve Duplicate
        ↓
Choose Canonical Asset
        ↓
Merge Metadata
        ↓
Retire OR Delete
        ↓
Resolve
```

Implementation tasks:

*Phase 2.4.5.1* — Update React logic. Add:
* ✅ Resolve modal state.
* ✅ Canonical asset selection state.
* ✅ Action selection state.
* ✅ Metadata merge toggle.
* ✅ Resolve API handler.
* ✅ Duplicate refresh after completion.

*Phase 2.4.5.2* — Build enterprise Resolve Duplicate modal.

Modal includes:
* ✅ Duplicate asset summary.
* ✅ Radio selection for canonical asset.
* ✅ Merge metadata checkbox.
* ✅ Action selection: Retire Duplicate / Delete Duplicate.
* ✅ Cancel button.
* ✅ Resolve button.

The modal submits: `POST /assets/resolve-duplicate`

*Phase 2.4.5.3* — Update:

```
frontend/src/styles/admindashboard.css
```

Add styling for:
* ✅ Resolve modal.
* ✅ Canonical asset selector.
* ✅ Radio group.
* ✅ Metadata checkbox.
* ✅ Resolve button.
* ✅ Responsive layout.

#### Verification Checklist

Backend completed:
* ✅ Duplicate metadata merging.
* ✅ AI tag merging.
* ✅ Searchable tag merging.
* ✅ SQL metadata synchronization.
* ✅ PostgreSQL synchronization.
* ✅ ChromaDB synchronization.
* ✅ Vector deletion.
* ✅ Admin RBAC.
* ✅ Backward compatibility.

Frontend completed:
* ✅ Resolve Duplicate modal.
* ✅ Canonical asset selection.
* ✅ Resolve API integration.
* ✅ Updated duplicate management UI.

---

### FEATURE 3.3: Expiry Date Reminder & Alert System
* **Status** Completed
* **Objective:** Automatically monitor assets using the `business.expiry_date` metadata field, determine expiry status, restrict expired assets when accessed, expose expiry information through asset APIs, and provide dedicated administrative monitoring endpoints.

* **Database / Schema:**
  * Pydantic Schema: Add `expired` or `expiring_soon` computed flags in asset response schemas.
* **Backend API:**
  * Route: `GET /admin/assets/expiring?days_threshold=30` returning assets where `metadata->'business'->>'expiry_date'` falls within the threshold or is in the past.
  * Route: `POST /admin/assets/{id}/check-expiry` to auto-restrict expired assets (`status = 'restricted'`) and create a record in `notifications` table.
* **Frontend UI:**
  * Update `AssetCard.jsx` and `AssetDetail.jsx` to parse `metadata.business.expiry_date`. If date is past, show a prominent red badge `EXPIRED`. If approaching within 30 days, show amber badge `EXPIRING SOON`. Add an "Expiring Assets" filter/tab in Admin Dashboard.

### Current Implementation Progress
### ✅ Completed

#### 1. Expiry Service

A dedicated expiry management service has been introduced.

**Location**

```text
backend/app/services/storage/expiry_service.py
```

**Responsibilities**

- Read expiry date from `asset_metadata.business.expiry_date`
- Parse `YYYY-MM-DD` formatted dates
- Ignore invalid or missing expiry dates
- Determine whether an asset is expired
- Determine whether an asset is expiring soon (default threshold: 30 days)
- Calculate remaining days until expiry
- Build reusable expiry status payloads
- Automatically restrict expired assets
- Generate notifications for all Admin and Super Admin users
- Retrieve all expired and expiring assets for administrative monitoring

Implemented methods:

```python
ExpiryService.get_expiry_date()

ExpiryService.is_expired()

ExpiryService.days_until_expiry()

ExpiryService.is_expiring_soon()

ExpiryService.build_expiry_status()

ExpiryService.auto_restrict_if_expired()

ExpiryService.get_expiring_assets()
```

---

#### 2. Asset Response Schema

**File**

```text
backend/app/schemas/asset_schema.py
```

`AssetResponse` now exposes computed expiry information.

Added fields:

```python
expired: bool = False

expiring_soon: bool = False

days_until_expiry: Optional[int] = None
```

These fields are computed dynamically by `ExpiryService` and are **not persisted** in the database.

---

#### 3. Asset Retrieval Integration

`GET /assets/{asset_id}` has been integrated with the expiry service.

Current flow:

```
Load Asset
      │
Permission Checks
      │
Restricted Access Validation
      │
Domain Validation
      │
ExpiryService.auto_restrict_if_expired()
      │
ExpiryService.build_expiry_status()
      │
Return enriched AssetResponse
```

Returned responses now include:

- expired
- expiring_soon
- days_until_expiry

Expired assets are automatically transitioned to `restricted` during retrieval if required.


## ✅ Completed Developments

All items for Feature 3.3 have been completed:

- ✅ Integrate expiry status into asset listing endpoints.
- ✅ Implement `GET /admin/assets/expiring`.
- ✅ Implement `POST /admin/assets/{asset_id}/check-expiry`.
- ✅ Add expiry dashboard components in the frontend.
- ✅ Add Expired / Expiring Soon badges in Asset Cards.
- ✅ Display expiry information on Asset Detail page.
- ✅ Add admin expiry filters.
- ✅ Complete frontend API integration.

---

## Design Notes

No database schema changes were required.

The expiry system relies entirely on:

```
asset.asset_metadata
    └── business
            └── expiry_date
```

The existing workflow status field is reused:

```
approved
draft
pending_review
archived
restricted
```

Expired assets transition to `restricted` automatically without introducing a new status enum.

---
---

### ✅ FEATURE 5.1: AuditLog Database Model & Migration
* **Objective:** Create the core compliance tracking table to log every significant user action (upload, review, delete, role change, metadata update).
* **Database / Schema:**
  * Create `backend/app/models/audit/audit_log_model.py`.
  * Table `audit_logs`:
    ```python
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # e.g., 'UPLOAD', 'APPROVE', 'REJECT', 'DELETE', 'ROLE_CHANGE'
    field_name = Column(String, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ```
  * Import in `backend/app/main.py` so `create_all` initializes it.
* **Backend Utility:**
  * Create helper function `log_audit_event(db: Session, user_id: str, action: str, asset_id: str = None, ...)` in `backend/app/utils/audit_logger.py`.

---

### ✅ FEATURE 5.2: Audit Log API Endpoints
* **Objective:** Expose queried and paginated audit logs for administrators and compliance officers.
* **Backend API:**
  * Route: `GET /admin/audit-logs` (Super Admin & Admin only).
  * Query Params: `asset_id: Optional[str]`, `user_id: Optional[str]`, `action: Optional[str]`, `from_date: Optional[str]`, `to_date: Optional[str]`, `page: int = 1`, `limit: int = 50`.
  * Pydantic Schema: `AuditLogResponse` and `PaginatedAuditLogs`.

---

### ✅ FEATURE 5.3: Audit Log UI Page
* **Objective:** Provide a dedicated interactive dashboard tab for viewing and filtering system audit logs.
* **Frontend UI:**
  * Create component `frontend/src/pages/admin/AuditLogViewer.jsx`.
  * Include multi-field filter inputs (User ID, Asset ID, Action dropdown, Date range picker).
  * Render data in a responsive data table with formatted timestamps and highlighted diffs for `old_value` vs `new_value`. Add tab to `AdminDashboard.jsx`.

---

### ✅ FEATURE 5.4: Unused Assets Report Endpoint & UI
* **Objective:** Identify stale or unused assets that have zero downloads or previews to optimize cloud storage costs.
* **Backend API:**
  * Route: `GET /admin/analytics/unused-assets?days=90`.
  * Logic: Query assets created over `days` ago where `id` does not exist in `asset_usage` table (or total `usage_count == 0`).
* **Frontend UI:**
  * Add "Unused Assets" view inside `AdminDashboard.jsx` under Analytics. Allow bulk selection to "Retire" or "Archive" selected unused assets.

---

### FEATURE 5.5: Missing Metadata Report Endpoint & UI
* **Objective:** Pinpoint low-quality assets with poor completeness scores to prompt content curation.
* **Backend API:**
  * Route: `GET /admin/analytics/missing-metadata?threshold=60`.
  * Logic: Query assets where `completeness_score < threshold` and `is_latest == True`.
* **Frontend UI:**
  * Add "Metadata Gaps" card/table in Admin Dashboard listing asset name, uploader, current completeness score (with progress bar), and a quick link to edit metadata.

---

### FEATURE 5.6: Time-to-Approval Analytics Report
* **Objective:** Measure workflow bottleneck metrics (average time spent in `pending_review` before being `approved` or `rejected`).
* **Backend API:**
  * Route: `GET /admin/analytics/approval-times`.
  * Logic: Query audit logs or asset creation/update timestamps to compute average duration by domain and reviewer.
* **Frontend UI:**
  * Display average turnaround time stat cards and breakdown table in Admin Dashboard.

---

### FEATURE 5.7: Content Coverage Gap Report
* **Objective:** Track search terms that return 0 or very few results to inform marketing teams what assets need to be produced.
* **Database / Schema:**
  * Create model `search_logs` (`id`, `query`, `search_type`, `results_count`, `user_id`, `timestamp`).
  * Wire logging into `/search/semantic` and `/search/hybrid` routes.
* **Backend API:**
  * Route: `GET /admin/analytics/search-gaps?min_results=2`.
  * Logic: Return top search queries where `results_count < min_results`.
* **Frontend UI:**
  * Render a "Content Gaps (Failed Searches)" table in Admin Analytics.

---

### FEATURE 5.8: CSV Export Functionality for Reports
* **Objective:** Allow one-click CSV export for all admin analytics tables.
* **Backend API:**
  * Route: `GET /admin/analytics/export?report_type=unused|missing_meta|audit|most_used`.
  * Logic: Use Python `csv.writer` or `io.StringIO` inside a `StreamingResponse(..., media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})`.
* **Frontend UI:**
  * Add "Export CSV" icon buttons above tables in `AdminDashboard.jsx`.

---

### ✅ FEATURE 6.1: Adaptive Upload Wizard (Dynamic Fields by Asset Type)
* **Objective:** Make Step 3 (Business Metadata) dynamically show/require specific fields based on the selected `asset_type` in Step 2.
* **Frontend UI:**
  * Modify `frontend/src/pages/admin/UploadAsset.jsx`.
  * Implement conditional rendering dictionary:
    * If `video` or `social_creative`: Require `campaign` and `duration/channel`.
    * If `brochure` or `campaign_file`: Require `campaign`, `service_line`, and `expiry_date`.
    * If `pitch_deck`: Require `audience` and `use_case`.
    * If `logo` or `brand_guideline`: Require `domain` and `usage_rights`.

---

### ✅ FEATURE 6.2: Drag-and-Drop Upload Zone
* **Objective:** Upgrade the standard file selector in Step 1 of `UploadAsset.jsx` to a smooth drop zone.
* **Frontend UI:**
  * Update Step 1 in `UploadAsset.jsx`.
  * Add `onDragOver`, `onDragLeave`, and `onDrop` handlers with visual border highlighting and file validation (checking MIME type against allowed file types).

---

### ✅ FEATURE 6.3: Batch Upload & Progress Queue
* **Objective:** Enable multi-file selection with a staged upload queue so users can upload 5-10 assets sequentially.
* **Frontend UI:**
  * Allow `multiple` file selection in drop zone.
  * Render an upload queue sidebar/panel showing individual progress bars, status badges (Analyzing AI -> Uploading -> Ready for Review), and per-file metadata override toggles.

---

### ✅ FEATURE 6.4: Video-Specific Fields & Metadata
* **Objective:** Capture specialized video attributes during upload and display them in asset details.
* **Database / Schema:**
  * Add fields to JSONB `asset_metadata['content']`: `duration_seconds: int`, `transcript: str`, `aspect_ratio: str`.
* **Backend Logic:**
  * Update `asset_service.py` to extract basic video properties or accept client-provided transcript/duration during upload.
* **Frontend UI:**
  * Render video duration badge on `AssetCard.jsx`. Render expandable "Video Transcript" box on `AssetDetail.jsx`.

--- 

### ✅ FEATURE 7.1: Website & Marketing Context Flag Fields
* **Objective:** Add explicit governance flags for website and public campaign safety.
* **Database / Schema:**
  * Add to `_ASSET_COLUMNS` in `migrate.py`:
    ```python
    ("website_safe", "BOOLEAN DEFAULT FALSE"),
    ("public_use_approved", "BOOLEAN DEFAULT FALSE"),
    ("brand_aligned", "BOOLEAN DEFAULT TRUE"),
    ("alt_text", "TEXT"),
    ```
  * Update `Asset` SQLAlchemy model with these columns.
* **Backend API & Search:**
  * Expose these flags in asset creation/review endpoints and enable filtering by `website_safe=True` in asset listings.
* **Frontend UI:**
  * Add checkboxes in Reviewer Queue (`ReviewQueue.jsx`) to toggle `website_safe` and `public_use_approved` during approval. Show green shield badges on approved cards.

---

### ✅ FEATURE 7.2: Asset Usage Context Linking Table
* **Objective:** Track exact external live placements of assets (e.g., "Live on Landing Page X", "Used in Email Campaign Y").
* **Database / Schema:**
  * Create table `asset_placements`:
    ```python
    id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False, index=True)
    platform = Column(String)  # e.g., 'Website', 'HubSpot Email', 'LinkedIn Ad'
    placement_url_or_id = Column(String)
    added_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ```
* **Backend API:**
  * Routes: `POST /assets/{id}/placements` and `GET /assets/{id}/placements`.
* **Frontend UI:**
  * Add "Live Placements" section in `AssetDetail.jsx` showing active links where the asset is deployed.

---

### ✅ FEATURE 7.3: Web-Ready Output Generation on Download
* **Objective:** On download, allow users to choose on-the-fly transformations (e.g., WebP conversion, 1080p resize) via Cloudinary URL transformation parameters.
* **Backend API:**
  * Update `GET /assets/{id}/download`. Accept query params: `format=webp|jpg|png`, `width=int`, `quality=auto|low|high`.
  * If asset is hosted on Cloudinary (`storage_path` contains `res.cloudinary.com`), inject transformation string (e.g., `/f_webp,q_auto,w_1080/`) into URL before returning redirect/stream.
* **Frontend UI:**
  * In `AssetDetail.jsx`, convert the Download button into a dropdown menu: "Download Original", "Download Web-Ready (WebP, 1080p)", "Download Thumbnail (400px)".

---

### FEATURE 8.1: Webhook System for Asset Status Changes
* **Objective:** Broadcast real-time HTTP POST notifications to external systems (CMS, Slack, Zapier) whenever asset status changes (`published`, `approved`, `rejected`).
* **Database / Schema:**
  * Create model `webhooks` (`id`, `url`, `secret`, `events: ARRAY[str]`, `is_active: bool`, `created_at`).
* **Backend Logic:**
  * Create `webhook_service.py` with async/background HTTP POST dispatcher triggered inside reviewer approval/publish routes. Include HMAC signature header `X-DAM-Signature`.
* **Frontend UI:**
  * Create Webhooks Management tab inside Super Admin / Admin Dashboard to register URLs and select event triggers.

---

### FEATURE 8.2: External API Key System
* **Objective:** Enable programmatic API access for external headless CMS or CI/CD pipelines without user JWT login.
* **Database / Schema:**
  * Create table `api_keys` (`id`, `key_prefix`, `hashed_key`, `name`, `allowed_domains: ARRAY[str]`, `created_by`, `is_active`).
* **Backend Security:**
  * Create authentication dependency `get_api_key_or_jwt_user` in `auth_dependency.py` that checks for `X-API-Key` header, hashes it, compares against active keys, and grants scoped read/search permissions.
* **Frontend UI:**
  * Add "API Keys" management page/modal in Super Admin Dashboard with key generation and copy-once display.

---

### FEATURE 8.3: `external_id` Mapping Field & CMS Sync
* **Objective:** Link DAM assets to 3rd-party CMS entries (e.g., Contentful asset ID or WordPress ID).
* **Database / Schema:**
  * Add column `("external_id", "VARCHAR")` and `("cms_source", "VARCHAR")` to `_ASSET_COLUMNS` in `migrate.py` and `Asset` model.
* **Backend API:**
  * Route: `GET /assets/by-external-id/{cms_source}/{external_id}` for instant CMS lookup.
  * Allow PATCHing `external_id` and `cms_source` on existing assets.

---

## SECTION 5: FINAL VERIFICATION CHECKLIST BEFORE COMPLETING ANY TASK

Whenever an LLM finishes building any single feature above, it MUST run through this final self-audit:
1. [ ] **No Alembic files created?** Verified schema changes were added to `migrate.py` and SQLAlchemy model.
2. [ ] **No Tailwind or inline styling mess?** Verified all new styling uses clear, structured classes in Vanilla CSS files in `frontend/src/styles/`.
3. [ ] **ChromaDB Sync Kept Intact?** If metadata or asset attributes were changed/merged, verified vector embeddings/store index were updated.
4. [ ] **RBAC Role Protection Applied?** Verified endpoint includes `Depends(get_current_user)` and required role checks.
5. [ ] **No Breaking Changes to Existing Endpoints?** Verified backward compatibility for frontend screens (`AssetBrowser`, `AssetDetail`, `UploadAsset`).