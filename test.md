# AI-DAM: Comprehensive Testing Roadmap

This document provides a step-by-step guide to testing all the core features and workflows built into the AI-DAM platform. 

---

## 1. Authentication & Role-Based Access (RBAC)
**Goal:** Verify that different user roles have appropriate access to the system.
- [ ] **Login as Admin:** Navigate to `/login` and log in with an Admin account. Verify you are redirected to the Admin Dashboard.
- [ ] **Login as User:** Log in with a standard User account. Verify you are redirected to the Asset Browser and do *not* have access to Admin routes.
- [ ] **Login as Reviewer:** Log in with a Reviewer account. Verify you have access to the Review Queue but not system-wide admin settings.

---

## 2. Asset Ingestion & AI Metadata (Phase 1 & 2)
**Goal:** Test the upload process and verify AI-powered metadata extraction.
- [ ] **Upload a New Asset:** Go to **Upload New Asset**. Drag and drop an image or video file.
- [ ] **AI Extraction:** Wait for the AI to analyze the file. Verify that fields like `Perceptual Hash`, `AI Summary`, `Detected Objects`, and `Alt Text` are auto-populated.
- [ ] **Taxonomy & Governance:** Manually adjust the `Domain`, `Campaign`, and `Usage Rights` (e.g., set an expiration date). Submit the asset.
- [ ] **Review Queue (If Draft):** If the asset was uploaded as a draft, log in as a Reviewer, navigate to the **Review Queue**, and approve it.

---

## 3. Master & Derivative Relationships (Phase 1 & 2)
**Goal:** Ensure the system correctly handles parent/child asset relationships.
- [ ] **View Master Asset:** Go to the Asset Browser, click on your newly approved asset to open the Asset Detail view.
- [ ] **Upload a New Version:** In the Asset Detail view, find the "Versions & Renditions" tab. Click **Upload New Version**.
- [ ] **Verify Relationship:** Upload a cropped or resized version of the original image. Once approved, verify that it appears as a *Derivative* under the original *Master* asset, and the Master asset shows the Derivative in its hierarchy.

---

## 4. Advanced Search & Discovery (Phase 3)
**Goal:** Test the hybrid semantic search capabilities.
- [ ] **Keyword Search:** In the Asset Browser, type an exact filename or tag into the search bar. Verify the asset appears immediately.
- [ ] **Semantic Search:** Toggle the search mode to **Semantic**. Type a descriptive query (e.g., "a sunny landscape" or "marketing banner with a laptop"). Verify that the AI returns contextually relevant assets even if the exact keywords aren't in the title.
- [ ] **Faceted Filtering:** Use the left sidebar to filter by `Domain`, `Asset Type`, or `Status`. Ensure the grid updates in real-time.

---

## 5. Bulk Actions & Admin Dashboard (Phase 3)
**Goal:** Verify the ability to manage assets at scale.
- [ ] **Enter Bulk Edit Mode:** In the Admin Dashboard, click **Enter Bulk Edit Mode**.
- [ ] **Select Assets:** Select multiple assets using the checkboxes.
- [ ] **Apply Bulk Edits:** Click the bulk edit button, change the `Domain` or `Status` for all selected assets, and save. Verify the changes are applied across all selected items.
- [ ] **Duplicate Detection:** Navigate to the **Duplicates Scan** tab in the Admin Dashboard. Verify that identical assets (based on perceptual hash) are flagged, and test the "Resolve" merging process.
- [ ] **Expiring Assets:** Navigate to the **Expiring Assets** tab. Ensure assets with an expiration date within 30 days are listed correctly.

---

## 6. Secure External Sharing (Phase 4)
**Goal:** Test the ability to share assets securely with external parties.
- [ ] **Generate Link:** In the Asset Browser, open an asset and click the **Share** button.
- [ ] **Configure Security:** Set an expiration time (e.g., 7 days) and a password. Click **Generate Link**.
- [ ] **Test the Link:** Open an Incognito/Private browsing window and paste the generated link.
- [ ] **Password Protection:** Verify that you are prompted for a password. Enter the password and confirm you can view and download the asset.
- [ ] **Expiration Testing (Optional):** If possible, generate a link that expires immediately (or manually alter the DB) to verify that expired links return a 410 Gone error.

---

## 7. UI Polish & Aesthetics (Phase 5)
**Goal:** Validate the visual quality and premium feel of the platform.
- [ ] **Glassmorphism Theme:** Verify that the top navigation bar and sidebars use a translucent, blurred glass effect (`.glass-panel`).
- [ ] **Micro-animations:** Hover over asset cards in the browser. Verify they smoothly tilt/flip in 3D and have a subtle glowing shadow.
- [ ] **Typography & Gradients:** Ensure the "Outfit" font is rendering correctly globally, and primary buttons (like Upload/Search) use the new gradient `.btn-premium` styling with hover lifts.
- [ ] **Responsive Design:** Resize your browser window to simulate a tablet/mobile view. Ensure the grid gracefully collapses and the sidebar is toggleable. 

---

## 8. Audit Logging & Analytics
**Goal:** Ensure all actions are tracked for compliance.
- [ ] **View Audit Logs:** As an Admin, navigate to the **Audit Logs** tab in the dashboard.
- [ ] **Verify Events:** Confirm that your recent actions (Login, Asset Upload, Bulk Edit, Link Generation) are recorded with the correct timestamps and user IDs.
