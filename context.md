# AI-DAM — Complete Project Context for LLM

> **Purpose:** This document is the single source of truth for the AI-DAM project.
> Feed it to any LLM to understand the full system state, what is already built, what is missing,
> and in what order to build the remaining features.
>
> **Last updated:** 2026-07-02
> **Overall completion:** ~71% of the full plan (Phases 1 and 4 complete, Phases 2 & 3 at 88%, Phases 5-8 unbuilt)

---

## 1. Project Overview

**AI-DAM** is a full-stack AI-powered Digital Asset Management (DAM) platform built for enterprise marketing & content teams.

Its core purpose is to:
- Store, organize, and retrieve digital assets (images, videos, PDFs, documents)
- Use AI to auto-tag, describe, OCR, and deduplicate assets
- Enforce a multi-role approval workflow before assets go live
- Provide hybrid semantic + keyword search across all assets
- Control access by role and by business domain (e.g., Healthcare, Finance, Marketing)

---

## 2. Tech Stack (ACTUAL — as deployed)

| Layer | Technology |
|---|---|
| **Frontend** | React + Vite (JavaScript, JSX) |
| **Styling** | Vanilla CSS (per-component CSS files in `frontend/src/styles/`) |
| **State Management** | React Context API |
| **Backend API** | FastAPI (Python) |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy (sync) |
| **Migrations** | Custom self-healing DDL script (`db/migrate.py`) — NOT Alembic |
| **Vector Search** | ChromaDB (NOT pgvector) |
| **File Storage** | Local Filesystem (`STORAGE_BACKEND="local"` in `storage/` directory; architecture ready for transition to AWS S3 bucket). Supports all file types |
| **AI / LLM** | Groq API with Llama model (auto-tagging, metadata suggestion, summarization) |
| **Embeddings** | Sentence Transformers (local) |
| **OCR** | Tesseract / PyMuPDF |
| **Thumbnail Generation** | Pillow + FFmpeg |
| **Authentication** | JWT (Bearer token, httpOnly cookie support) |
| **Rate Limiting** | SlowAPI |
| **Perceptual Hashing** | Custom dHash (16-char hex) in `backend/app/utils/image_hash.py` |

> WARNING: `techstack.md` in the repo lists Next.js, pgvector, Alembic, Redis, Celery — these were PLANNED but NOT implemented.
> The actual stack is React+Vite, ChromaDB, and custom DDL migrations. Do NOT rely on techstack.md.

---

## 3. Directory Structure (Key Files)

```
AI-DAM/
├── backend/
│   └── app/
│       ├── main.py                           # FastAPI entry, router registration, CORS, rate limiting
│       ├── api/routes/
│       │   ├── asset_routes.py               # Upload, list, detail, submit-for-review, retire, similar, duplicate-candidates
│       │   ├── auth_routes.py                # Register, login, logout, /me
│       │   ├── admin_routes.py               # Admin asset management, analytics, notifications
│       │   ├── reviewer_routes.py            # Approve, reject, publish, restrict, unrestrict
│       │   ├── super_admin_routes.py         # User management, role changes, domain assignment
│       │   └── search_routes.py              # Semantic + hybrid search
│       ├── api/dependencies/
│       │   └── auth_dependency.py            # JWT decode, role guards, upload permission gate
│       ├── models/
│       │   ├── asset/asset_model.py          # Core Asset SQLAlchemy model (all columns)
│       │   ├── user/user_model.py            # User model with roles + allowed_domains
│       │   ├── user/notification_model.py    # Admin rejection notification model
│       │   └── analytics/asset_usage_model.py  # Usage tracking (download/preview counts)
│       ├── schemas/
│       │   ├── metadata/metadata_enums.py    # AssetStatus, AssetTypes, DomainType, etc.
│       │   ├── metadata/metadata_schema.py   # MandatoryMetadata, BusinessMetadata, ContentMetadata, AIEnrichmentMetadata
│       │   ├── user/schemas.py               # Auth, Review, Publish, Restrict, Notification Pydantic schemas
│       │   └── search_schema.py              # SearchFilters, SemanticSearchRequest, HybridSearchRequest + results
│       ├── services/storage/
│       │   └── asset_service.py              # Core upload pipeline: hash, local/cloud storage backend, AI enrichment, completeness
│       ├── ai/
│       │   ├── embeddings/                   # Sentence transformer embedding pipeline
│       │   ├── ocr/                          # Tesseract OCR
│       │   ├── pipelines/                    # AI enrichment orchestration
│       │   ├── retrieval/
│       │   │   ├── hybrid_search_service.py  # 0.6 keyword + 0.4 semantic merge
│       │   │   ├── keyword_search_service.py
│       │   │   └── semantic_search_service.py
│       │   ├── tagging/                      # LLM auto-tagging via Groq
│       │   └── vectorstore/                  # ChromaDB integration
│       ├── db/
│       │   ├── session/database.py           # SQLAlchemy engine + session factory
│       │   └── migrate.py                    # Self-healing ADD COLUMN IF NOT EXISTS migrations (run at startup)
│       └── utils/
│           ├── image_hash.py                 # dHash perceptual hash computation
│           ├── completeness.py               # Metadata completeness score (0-100)
│           ├── file_utils.py                 # File handling helpers
│           └── image_utils.py               # Image processing helpers
│
└── frontend/
    └── src/
        ├── App.jsx                           # React Router v6 routes, role-based protected routes
        ├── pages/
        │   ├── Login.jsx / Register.jsx
        │   ├── admin/
        │   │   ├── AdminDashboard.jsx        # Asset list, delete, analytics
        │   │   └── UploadAsset.jsx           # 4-step upload wizard with AI pre-fill
        │   ├── reviewer/
        │   │   └── ReviewQueue.jsx           # Approve/reject/publish/restrict queue
        │   ├── user/
        │   │   ├── AssetBrowser.jsx          # Grid view, hybrid+semantic search, faceted filters
        │   │   └── AssetDetail.jsx           # Full detail: metadata, versions, completeness, AI enrichment
        │   └── superadmin/
        │       ├── SuperAdminDashboard.jsx
        │       └── UserManagement.jsx        # Role changes, domain assignment, activate/deactivate
        └── components/common/
            ├── AssetCard.jsx                 # Status badges, AI-tagged badge, missing-metadata warning
            ├── AssetModal.jsx                # Quick-view modal
            ├── Navbar.jsx
            ├── Sidebar.jsx
            └── NotificationBell.jsx          # Unread count, mark-read dropdown
```

---

## 4. Data Models

### 4.1 Asset (`assets` table)

```python
id                  String (UUID PK)
original_filename   String
stored_filename     String
mime_type           String
file_size           Integer
file_hash           String (SHA256, for exact-dupe blocking)
storage_path        String (Cloudinary URL)
thumbnail_path      String (nullable)
preview_path        String (nullable)
asset_metadata      JSONB   # full nested metadata blob (see 4.2)
status              String  # draft | pending_review | approved | rejected | published | restricted | archived
version             Integer (default 1)
parent_id           String (FK -> assets.id, nullable) # previous version
root_asset_id       String (nullable) # first version in chain
is_latest           Boolean (default True)
is_archived         Boolean (default False)

# AI Retrieval — queryable individual columns (duplicated out of JSONB for direct SQL filtering)
perceptual_hash     String(16)       # 16-char hex dHash (images only)
ai_summary          Text             # LLM-generated 1-2 sentence summary
completeness_score  Integer (0-100)  # weighted score across 13 metadata fields
ai_tags             JSONB            # list[str] of AI-generated tags
detected_objects    JSONB            # list[str] of detected objects
extracted_text      Text             # OCR output
image_caption       Text             # BLIP/LLM image caption

# Version Control — per-version changelog
changelog           Text             # human-readable "what changed in this version"
updated_by          String           # username/user_id of uploader

# Timestamps
created_at          DateTime(timezone=True) server_default=now()
updated_at          DateTime(timezone=True) onupdate=now()
```

### 4.2 asset_metadata JSONB Schema

```json
{
  "mandatory": {
    "asset_name": "string",
    "asset_type": "image | video | pdf | document",
    "description": "string",
    "created_by": "string (free-text, NOT linked to user.id)",
    "usage_rights": "string (free-text, NOT enum-controlled)",
    "owner": "string (free-text, NOT linked to user.id)"
  },
  "business": {
    "domain": "AI | Staffing | Marketing | Sales | Finance | HR | Operations | Healthcare | Tech | Design",
    "use_case": "email | presentation | website | campaign | sales | social_media | advertisment",
    "audience": "b2b | enterprise | startup | consumer | partner",
    "funnel_stage": "awareness | consideration | conversion",
    "service_line": "string (optional, added Phase 1)",
    "geography": "string (optional, added Phase 1)",
    "campaign": "string (optional, added Phase 1)",
    "language": "string (optional, added Phase 1)",
    "channel": "string (optional, added Phase 1)",
    "expiry_date": "string (optional, stored as plain string — NO date validation)"
  },
  "content": {
    "keywords": ["list", "of", "strings"],
    "visual_elements": ["list", "of", "strings"],
    "tone": "professional | casual | technical | formal | friendly | creative"
  },
  "ai_enrichment": {
    "ai_tags": ["list"],
    "extracted_text": "string",
    "image_caption": "string",
    "detected_objects": ["list"],
    "searchable_tags": ["list"],
    "enrichment_status": "string",
    "ai_summary": "string"
  }
}
```

### 4.3 User (`users` table)

```python
id               String (UUID PK)
email            String (unique, indexed)
full_name        String
hashed_password  String (bcrypt)
role             String  # one of the 10 roles below
allowed_domains  ARRAY(String)  # null = no restriction; ["Healthcare","Finance"] = domain-scoped
is_active        Boolean (default True)
created_at       DateTime
```

**Valid Roles (10 total):**

| Role | Permissions |
|---|---|
| `super_admin` | Full system access |
| `admin` | Upload, manage assets, manage users |
| `reviewer` | Approve / reject / publish / restrict assets |
| `marketing_manager` | Upload, view all approved, manage campaigns |
| `designer` | Upload, view all approved assets |
| `content_lead` | Upload, curate content, view analytics |
| `sales_user` | View approved assets, download for sales use |
| `website_team` | Upload & manage website-safe assets |
| `external_partner` | Restricted view of approved assets only |
| `user` | Browse & download approved assets only |

**Domain-scoped access:** If `allowed_domains` is set (e.g. `["Healthcare"]`), the asset list endpoint
filters out assets whose `business.domain` is NOT in that list. Null = sees all domains.

### 4.4 AssetUsage (`asset_usage` table)

```python
id          String (UUID PK)
asset_id    String (FK -> assets.id, indexed)
action      String   # "download" | "preview" | "search"
usage_count Integer  # incremented on each action
created_at  DateTime
user_id     String   # (Phase 1.3) Tracks which user performed the action (download/preview)
```

### 4.5 Notification (`notifications` table)

Stores admin alerts triggered by reviewer rejection.

```python
id         String (UUID PK)
asset_id   String
message    String
reason     String (nullable)
is_read    Boolean (default False)
created_at DateTime
```

### 4.6 completeness_score Calculation

Scored across 13 weighted fields (total = 100 points):

| Section | Fields | Weight Each |
|---|---|---|
| mandatory | asset_name, asset_type, description | 10 pts |
| mandatory | created_by, usage_rights, owner | 8 pts |
| business | domain, use_case, audience, funnel_stage | 8 pts |
| content | keywords, visual_elements | 6 pts |
| content | tone | 2 pts |

Implemented in `backend/app/utils/completeness.py`.

---

## 5. API Endpoints

### Auth (`/auth`)
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register new user (default role: `user`) |
| POST | `/auth/login` | Login -> JWT token |
| POST | `/auth/logout` | Clear cookie |
| GET | `/auth/me` | Current user info |

### Assets (`/assets`)
| Method | Path | Description |
|---|---|---|
| POST | `/assets/analyze` | AI pre-fill: analyze file BEFORE upload, returns suggested metadata |
| POST | `/assets/upload` | Upload asset (multipart/form-data + metadata JSON) |
| GET | `/assets/` | List assets (role-filtered, domain-filtered, supports faceted query params) |
| GET | `/assets/{id}` | Get single asset detail |
| PATCH | `/assets/{id}/submit-for-review` | Move status: draft -> pending_review |
| PATCH | `/assets/{id}/retire` | Retire asset (is_latest=False, hidden from search) |
| GET | `/assets/{id}/versions` | Full version history for an asset tree |
| GET | `/assets/{id}/similar` | Find visually similar assets via perceptual hash (dHash) |
| GET | `/assets/duplicate-candidates` | Scan all assets for near-duplicate pairs |
| GET | `/assets/{id}/download` | Download asset file |
| DELETE | `/assets/{id}` | Delete asset (admin+ only) |

### Reviewer (`/reviewer`)
| Method | Path | Description |
|---|---|---|
| GET | `/reviewer/queue` | Get all pending_review assets |
| POST | `/reviewer/assets/{id}/approve` | Approve -> `approved` |
| POST | `/reviewer/assets/{id}/reject` | Reject with `reason` + `rejection_category` |
| POST | `/reviewer/assets/{id}/publish` | Publish -> `published` (with channels list) |
| POST | `/reviewer/assets/{id}/restrict` | Restrict -> `restricted` (with restricted_to_roles list) |
| POST | `/reviewer/assets/{id}/unrestrict` | Unrestrict -> back to `approved` |

### Search (`/search`)
| Method | Path | Description |
|---|---|---|
| POST | `/search/semantic` | Semantic search (ChromaDB) with faceted filters |
| POST | `/search/hybrid` | Hybrid search (0.6 keyword + 0.4 semantic) with faceted filters |

### Admin (`/admin`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/assets` | All assets with full management view |
| DELETE | `/admin/assets/{id}` | Delete asset |
| GET | `/admin/analytics/most-used` | Most-used assets report |
| GET | `/admin/notifications` | Admin notifications |
| PATCH | `/admin/notifications/{id}/read` | Mark single notification read |
| PATCH | `/admin/notifications/read-all` | Mark all notifications read |

### Super Admin (`/super-admin`)
| Method | Path | Description |
|---|---|---|
| GET | `/super-admin/users` | List all users |
| PATCH | `/super-admin/users/{id}/role` | Change user role |
| PATCH | `/super-admin/users/{id}/deactivate` | Deactivate user |
| PATCH | `/super-admin/users/{id}/reactivate` | Reactivate user |
| PATCH | `/super-admin/users/{id}/domains` | Assign allowed_domains to user |

---

## 6. Workflow / Status Lifecycle

```
[UPLOAD] -> draft
    |
    v
[PATCH /submit-for-review]
    |
    v
pending_review
    |
    |--[reviewer reject]--> rejected
    |                           (user can re-upload as new version)
    |
    |--[reviewer approve]--> approved
                                |
                                |--[reviewer publish]--> published
                                |
                                |--[reviewer restrict]--> restricted
                                                            |
                                                            |--[reviewer unrestrict]--> approved

[any status] --[admin retire]--> (is_latest=False, hidden from default listing)
[any status] --[set is_archived=True]--> hidden from search (PATCH /assets/{id}/archive, gap 1.5/3.2)
```

---

## 7. Search Architecture

- **Keyword Search**: PostgreSQL full-text search on `asset_metadata` JSONB fields
- **Semantic Search**: ChromaDB vector store with Sentence Transformer embeddings
- **Hybrid Search**: Weighted merge: `final_score = 0.6 * keyword_score + 0.4 * semantic_score`
- **Faceted Filters** (`SearchFilters` schema applied to both search types):
  - `domain` — filters by business.domain
  - `status` — filters by asset status (approved, published, etc.)
  - `asset_type` — filters by mandatory.asset_type
  - `geography` — filters by business.geography
  - `campaign` — filters by business.campaign
  - `language` — filters by business.language
- **Field-scoped search**: `search_field` param scopes the search to a specific metadata key
  - e.g. `search_field="campaign"` searches only within campaign values
- **Match explanation**: Every result includes `match_explanation` string
- **Result schema includes**: `completeness_score`, `ai_summary`, `perceptual_hash`, `match_explanation`

---

## 8. AI Pipeline (Per Upload — runs synchronously)

1. **SHA256 hash** — exact duplicate check; blocks re-upload if hash already exists
2. **dHash (perceptual hash)** — 16-char hex fingerprint stored for near-duplicate detection (images only)
3. **Storage persistence** — file stored locally (`STORAGE_BACKEND="local"`) or in cloud storage; path saved as `storage_path`
4. **Thumbnail/preview generation** — Pillow for images, FFmpeg for video frames, PyMuPDF for PDF page-1
5. **AI Enrichment** (via Groq/Llama):
   - OCR (Tesseract) for images/PDFs -> `extracted_text`
   - Image captioning -> `image_caption`
   - Object detection -> `detected_objects`
   - Auto-tagging -> `ai_tags`
   - LLM summary -> `ai_summary`
6. **Completeness score** — calculated from 13 weighted metadata fields -> `completeness_score` (0-100)
7. **ChromaDB indexing** — asset embedded and inserted into vector store for semantic search

> IMPORTANT: No background job queue (no Celery/Redis). All AI steps run synchronously at upload time.
> Large files will cause slow upload responses.

---

## 9. Frontend Pages & Components

### Pages by Role
| Page | Who Can Access | File |
|---|---|---|
| Login / Register | Public | `pages/Login.jsx`, `pages/Register.jsx` |
| Asset Browser | All authenticated users | `pages/user/AssetBrowser.jsx` |
| Asset Detail | All authenticated users | `pages/user/AssetDetail.jsx` |
| Upload Asset (4-step wizard) | admin, marketing_manager, designer, content_lead, website_team | `pages/admin/UploadAsset.jsx` |
| Admin Dashboard | admin, super_admin | `pages/admin/AdminDashboard.jsx` |
| Review Queue | reviewer | `pages/reviewer/ReviewQueue.jsx` |
| Super Admin Dashboard | super_admin | `pages/superadmin/SuperAdminDashboard.jsx` |
| User Management | super_admin | `pages/superadmin/UserManagement.jsx` |

### Key Components
| Component | Description |
|---|---|
| `AssetCard.jsx` | Thumbnail card with ALL status badges (draft, pending_review, approved, rejected, published, restricted, archived), AI-tagged badge, missing-metadata warning indicator |
| `AssetModal.jsx` | Quick-view overlay modal with full metadata display |
| `AssetBrowser.jsx` | Grid layout with hybrid/semantic toggle, faceted filter sidebar (domain, asset_type, geography, language — NOTE: no status filter yet) |
| `AssetDetail.jsx` | Full dedicated page: all metadata sections, version history list, completeness score ring/bar, AI enrichment panel |
| `NotificationBell.jsx` | Unread count badge in navbar, dropdown list of alerts, mark-read actions |
| `ReviewQueue.jsx` | Paginated queue of pending_review assets with approve/reject/publish/restrict action buttons |
| `UserManagement.jsx` | User table with inline role dropdown, domain assignment UI, activate/deactivate toggles |

### Upload Wizard (UploadAsset.jsx — 4 steps)
1. **Upload** — file picker, calls `/assets/analyze` for AI pre-fill
2. **Mandatory** — asset_name, asset_type, description, created_by, usage_rights, owner
3. **Business** — domain, use_case, audience, funnel_stage, service_line, geography, campaign, language, channel, expiry_date
4. **Content** — keywords, visual_elements, tone

---

## 10. Analysis Results — Built vs. Remaining

### DONE — Already Implemented (27 confirmed items)

| # | Plan Item | Evidence (file + line) |
|---|---|---|
| 1 | `service_line`, `geography`, `campaign`, `language`, `channel`, `expiry_date` metadata fields | `metadata_schema.py` L31-36 in BusinessMetadata |
| 2 | `updated_at` timestamp on Asset | `asset_model.py` L87-92 with `onupdate=func.now()` |
| 3 | `perceptual_hash` (dHash) column on Asset | `asset_model.py` L61 + `utils/image_hash.py` |
| 4 | Near-duplicate detection via perceptual hash | `GET /assets/{id}/similar` in `asset_routes.py` L447-510 |
| 5 | Duplicate candidate scanning endpoint | `GET /assets/duplicate-candidates` in `asset_routes.py` L632-699 |
| 6 | `ai_summary` stored as separate column | `asset_model.py` L64 + `metadata_schema.py` L55 |
| 7 | `completeness_score` column on Asset | `asset_model.py` L67 + `utils/completeness.py` |
| 8 | AI enrichment as queryable individual columns | `ai_tags`, `detected_objects`, `extracted_text`, `image_caption` on Asset model L70-73 |
| 9 | `pending_review`, `published`, `restricted` workflow routes | `reviewer_routes.py` L41-67 publish/restrict/unrestrict |
| 10 | "Submit for review" explicit action | `PATCH /assets/{id}/submit-for-review` in `asset_routes.py` L196-231 |
| 11 | Structured rejection feedback (`rejection_category`) | `ReviewRequest` schema in `schemas.py` L55-58 |
| 12 | Expanded roles: marketing_manager, designer, content_lead, sales_user, website_team, external_partner | `user_model.py` L44-54 + `super_admin_routes.py` L70-81 |
| 13 | Domain-scoped access (`allowed_domains` on User) | `user_model.py` L65-68 + domain filter in `asset_routes.py` L181-186 |
| 14 | `PATCH /super-admin/users/{id}/domains` | `super_admin_routes.py` L440-471 |
| 15 | Version history API endpoint | `GET /assets/{id}/versions` in `asset_routes.py` L388-438 |
| 16 | `changelog` + `updated_by` per version | `asset_model.py` L80-83 |
| 17 | Retire asset endpoint | `PATCH /assets/{id}/retire` in `asset_routes.py` L519-544 |
| 18 | Faceted filter schemas for search | `SearchFilters` in `search_schema.py` L30-41 |
| 19 | Search within specific metadata field | `search_field` param in `search_schema.py` L55-58 |
| 20 | Match explanation in search results | `match_explanation` in `BaseSearchResult` `search_schema.py` L23 |
| 21 | Status badges on asset cards (all statuses) | `AssetCard.jsx` L17-25 |
| 22 | Missing metadata warning on cards | `AssetCard.jsx` L57-59 `isMissingMeta` check |
| 23 | AI-tagged badge on cards | `AssetCard.jsx` L54 `hasAiEnrichment` check |
| 24 | Faceted filter UI in Asset Browser | `AssetBrowser.jsx` L21-26 domain/asset_type/geography/language filters |
| 25 | Asset Detail full page (not just modal) | `AssetDetail.jsx` — versions, completeness score, AI enrichment |
| 26 | Role-based view restriction in list endpoint | `asset_routes.py` L166-188 restricted roles see approved/latest only |
| 27 | `require_upload_permission` role gate | `auth_dependency.py` |

---

### NOT BUILT — Remaining Items by Phase

---

#### PHASE 1 — Foundation Fixes | 12 of 12 done | ALL COMPLETE ✅

| ID | Item | Status | Detail |
|---|---|---|---|
| 1.1 | Expand `AssetTypes` enum | DONE | `metadata_enums.py` L10-24 — 9 new types: banner, brochure, case_study, logo, social_creative, pitch_deck, brand_guideline, campaign_file, testimonial |
| 1.2 | Per-asset-class metadata rules | DONE | `asset_routes.py` — `_validate_asset_type_rules()` called at upload; video/social_creative need campaign or service_line; brochure/campaign_file need both; pitch_deck needs audience+use_case; logo/brand_guideline need domain |
| 1.3 | `user_id` on `AssetUsage` model | DONE | `asset_usage_model.py` + `migrate.py` (_ASSET_USAGE_COLUMNS); `log_usage()` updated; download + preview routes pass `current_user.id` |
| 1.4 | `archived_at` timestamp on Asset | DONE | `asset_model.py` + `migrate.py` — `archived_at` (DateTime) and `archive_reason` (Text) columns |
| 1.5 | `PATCH /assets/{id}/archive` route | DONE | `asset_routes.py` archive endpoint; Archive button (amber) in `AssetModal.jsx` (admin context only) |
| 1.6 | `usage_rights` as controlled vocabulary | DONE | `UsageRightsType` enum in `metadata_enums.py` (6 values); wired into `MandatoryMetadata`; `UploadAsset.jsx` uses `<select>` with labeled options |
| 1.7 | `created_by` / `owner` auto-populated from user | DONE | `UploadAsset.jsx` reads `user.full_name` from AuthContext; pre-fills both fields at mount; user can still override |

---

#### PHASE 2 — Search & Discovery | 7 of 8 done | 1 remaining

| ID | Item | Status | Detail |
|---|---|---|---|
| 2.1 | `status` filter in faceted search UI | DONE | `AssetBrowser.jsx` L392-404 — full STATUS_OPTIONS dropdown wired to filter state + search |
| 2.2 | Saved / recent searches | DONE | `AssetBrowser.jsx` L44-73 — localStorage `dam_recent_searches`, max 5, clear-all button |
| 2.3 | Duplicate candidate UI | DONE | `AdminDashboard.jsx` — "Duplicates Scan" tab with group cards, perceptual hash display, Retire + Delete per asset |
| 2.4 | Merge/replace workflow for duplicates | NOT BUILT | No API or UI to merge two assets into one canonical record — out of scope for now |

---

#### PHASE 3 — Version Control & Workflow | 7 of 8 done | 1 remaining

| ID | Item | Status | Detail |
|---|---|---|---|
| 3.1 | Version history UI (full tree) | DONE | `AssetDetail.jsx` L327-366 — clickable version tree with changelog, updated_by, date, Latest badge |
| 3.2 | Archive endpoint + UI | DONE | `PATCH /assets/{id}/archive` in `asset_routes.py`; Archive button in `AssetModal.jsx` (admin only, amber color) |
| 3.3 | Expiry reminder / alert system | NOT BUILT | `expiry_date` field exists in schema but no cron job or alert notification logic |
| 3.4 | Archived assets filtered from search | DONE | `keyword_search_service.py` — `.filter(Asset.is_archived == False)`; `semantic_search_service.py` — post-filter `if asset.is_archived: continue` |
| 3.5 | Archive reason field | DONE | `asset_model.py` + `db/migrate.py` — `archived_at` (DateTime) and `archive_reason` (Text) columns added |

---

#### PHASE 4 — Role & Permission Expansion | 6 of 6 done | ALL COMPLETE ✅

| ID | Item | Status | Detail |
|---|---|---|---|
| 4.1 | Per-asset access restriction enforcement | DONE | check_restricted_access helper added and called in get, list, download, preview, versions, similar, and search routes. |
| 4.2 | External partner time-limited access | DONE | access_expiry column added to User and verified in get_current_user token dependency. |
| 4.3 | Role-based approval scope | DONE | Reviewer check_reviewer_scope ensures domain restriction verification on all reviewer endpoints. |

---

#### PHASE 5 — Audit Trail & Reporting | 0 of 8 done | ALL UNBUILT

| ID | Item | Notes |
|---|---|---|
| 5.1 | `AuditLog` model | New table: `id`, `asset_id`, `user_id`, `action`, `field_name`, `old_value`, `new_value`, `timestamp` |
| 5.2 | Audit log API endpoints | `GET /admin/audit-log?asset_id=&user_id=&action=&from=&to=` |
| 5.3 | Audit log UI page | Searchable/filterable table in admin panel |
| 5.4 | Unused assets report | Assets where `AssetUsage.usage_count == 0` or no `AssetUsage` rows |
| 5.5 | Missing metadata report | Assets where `completeness_score < threshold` (e.g. < 60) |
| 5.6 | Time-to-approval analytics | Avg days from `created_at` (draft) to status change to `approved` |
| 5.7 | Content coverage gap report | Frequent search queries returning fewer than N results |
| 5.8 | CSV export | Download any report as `.csv` |

---

#### PHASE 6 — Smart Upload & Asset-Type Awareness | 0 of 4 done | ALL UNBUILT

> Prerequisite: Phase 1.1 (AssetTypes enum expansion) must be done first.

| ID | Item | Notes |
|---|---|---|
| 6.1 | Adaptive upload wizard | Step 3 (Business) should show different required fields depending on `asset_type` selected in Step 2 |
| 6.2 | Drag-and-drop upload | Replace click-only file input with a drop zone |
| 6.3 | Batch upload | Allow selecting multiple files; upload queue with progress per file |
| 6.4 | Video-specific fields | Add `duration`, `transcript`, `thumbnail_override` fields for video asset type |

---

#### PHASE 7 — Website & Marketing Context | 0 of 3 done | ALL UNBUILT

| ID | Item | Notes |
|---|---|---|
| 7.1 | Website/marketing flag fields | Add to Asset model: `website_safe` (bool), `public_use_approved` (bool), `brand_aligned` (bool), `alt_text` (string) |
| 7.2 | Asset usage context | "This asset is used on: [page X, campaign Y]" — requires CMS or manual linkage table |
| 7.3 | Web-ready output generation | Auto-generate a compressed/resized version on download for web use |

---

#### PHASE 8 — Integration Layer | 0 of 3 done | ALL UNBUILT

| ID | Item | Notes |
|---|---|---|
| 8.1 | Webhook system | Fire HTTP POST to registered URLs when asset status changes |
| 8.2 | External API key system | API key auth for headless/programmatic access without JWT login |
| 8.3 | `external_id` mapping field | Add `external_id` column to Asset for CMS sync (e.g., WordPress post ID, Contentful entry ID) |

---

## 11. Summary Scoreboard

| Phase | Description | Total Items | Done | Remaining | % Done |
|---|---|:---:|:---:|:---:|:---:|
| **1** | Foundation Fixes | 12 | 12 | 0 | **100%** |
| **2** | Search & Discovery | 8 | 7 | 1 | 88% |
| **3** | Version Control & Workflow | 8 | 7 | 1 | 88% |
| **4** | Role & Permission Expansion | 6 | 6 | 0 | **100%** |
| **5** | Audit Trail & Reporting | 8 | 0 | 8 | 0% |
| **6** | Smart Upload & Asset-Type Awareness | 4 | 0 | 4 | 0% |
| **7** | Website & Marketing Context | 3 | 0 | 3 | 0% |
| **8** | Integration Layer | 3 | 0 | 3 | 0% |
| | **TOTAL** | **52** | **37** | **15** | **~71%** |

---

## 12. Recommended Build Order (Immediate Next Steps)

### HIGH PRIORITY — Do First (security + compliance)

| Priority | ID | Task | Why |
|---|---|---|---|
| 1 | 5.1-5.3 | Build `AuditLog` model + API + UI | Compliance foundation — needed before scaling users |
| 2 | Phase 6 | Adaptive upload wizard | Types enum is ready, UX improvement |
| 3 | 2.4 | Merge/replace duplicate workflow | Complete Phase 2 to 100% |

### LOWER PRIORITY — Later

| Priority | ID | Task |
|---|---|---|
| 4 | Phase 5 (reports) | Analytics reports + CSV export |
| 5 | Phase 7 & 8 | Website context fields + Integration layer |

---

## 13. How to Add a New Column (Migration Pattern)

Since the project does NOT use Alembic, all schema changes follow this pattern:

**Step 1 — Add to `backend/app/db/migrate.py`:**
```python
_ASSET_COLUMNS: list[tuple[str, str]] = [
    # ... existing columns ...
    ("new_column_name", "VARCHAR"),   # <-- add here
]
```

**Step 2 — Add to the SQLAlchemy model (`asset_model.py`):**
```python
new_column_name = Column(String, nullable=True)
```

**Step 3 — Restart the backend** — `upgrade_db_schema()` runs at startup and executes
`ALTER TABLE assets ADD COLUMN IF NOT EXISTS new_column_name VARCHAR;` automatically.

No Alembic version files needed. The DDL is idempotent.

---

## 14. Known Technical Debt & Gotchas

1. **No Alembic** — Schema changes go through `db/migrate.py`. Add to `_ASSET_COLUMNS` or `_USER_COLUMNS`. Never touch the DB directly.

2. **No background job queue** — AI enrichment runs synchronously at upload. For large files this makes uploads slow. Celery+Redis is listed in `techstack.md` but NOT implemented.

3. **ChromaDB and PostgreSQL can desync** — If an asset is deleted from PostgreSQL but not from ChromaDB, semantic searches will return stale/orphaned results. A cleanup job is missing.

4. **`created_by` and `owner` are free-text** — No referential integrity to `users.id`. If a user is renamed or deleted, their attribution is orphaned. (Now auto-populated from logged-in user details on frontend, Phase 1.7).

5. **`expiry_date` is a plain string** — No date format validation, no scheduled check, no notification when an asset expires.

6. **Frontend is React+Vite, NOT Next.js** — Despite `techstack.md`. All routing is client-side React Router v6. There is no SSR.

7. **No test suite** — No unit tests, integration tests, or end-to-end tests exist anywhere in the codebase.

8. **ChromaDB and PostgreSQL can desync on update** — If metadata is edited in PostgreSQL, ChromaDB is not automatically re-indexed or updated. Search results can show outdated metadata until re-indexing occurs.

9. **Rate limiting is applied globally** via SlowAPI but per-endpoint limits are not clearly configured for all sensitive routes.

---

## 15. Environment & Deployment

| Aspect | Detail |
|---|---|
| Frontend deployment | Vercel (`ai-dam-six.vercel.app` and two alternate Vercel URLs) |
| Frontend local dev | `http://localhost:5173` (Vite default) |
| Backend CORS | Locked to: localhost:5173, localhost:3000, and the Vercel URLs above |
| Backend local dev | `http://localhost:8000` (FastAPI/uvicorn default) |
| Database | Hosted PostgreSQL (connection via `DATABASE_URL` env var) |
| File storage | Local Filesystem (`STORAGE_BACKEND=local`) with all file types supported; prepared for switch to S3 bucket |
| LLM | Groq API (configured via `GROQ_API_KEY` env var) |
| ChromaDB | Running locally or in a persistent Docker volume — no cloud hosted instance |
| Containerization | `Dockerfile` exists in repo root for backend containerization |

*End of AI-DAM context document. Total: ~71% complete. 15 items remaining. Phases 1 and 4 are 100% done. Phases 2 and 3 are 88% done.*
