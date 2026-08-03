# AI-DAM — AI-Powered Digital Asset Management

An intelligent digital asset management system that uses AI to automatically tag, categorize, and enrich media assets. Built for marketing teams, content creators, and brand managers.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python) |
| **Frontend** | React + Vite |
| **Database** | PostgreSQL |
| **Vector Search** | ChromaDB |
| **AI/ML** | Sentence Transformers, CLIP, BLIP, Tesseract OCR |
| **Cloud Storage** | Cloudinary (optional, supports local) |
| **Auth** | JWT (Bearer tokens) |

## Features

- **AI Auto-Tagging** — Automatic metadata generation for images, videos, PDFs, and documents
- **Semantic Search** — Find assets by meaning, not just keywords
- **Visual Similarity** — Perceptual hash-based duplicate and near-duplicate detection
- **Role-Based Access** — 10 roles from super admin to external partner
- **Version Control** — Full version history with changelog tracking
- **Review Workflow** — Draft → Pending Review → Approved/Rejected pipeline
- **Asset Governance** — Expiry dates, geographic/platform restrictions, brand alignment flags
- **Analytics** — Usage tracking, search gap analysis, approval time metrics
- **Audit Trail** — Full audit logging of all asset lifecycle events

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file in `backend/` — see **Environment Variables** below.

```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `backend/.env` with:

```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ai_dam
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# App
APP_NAME=AI-DAM
STORAGE_PATH=./storage

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# AI
GROQ_API_KEY=your-groq-api-key

# Cloudinary (optional — set STORAGE_BACKEND=local to skip)
STORAGE_BACKEND=local
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Super Admin Seed
SEED_SUPER_ADMIN_EMAIL=admin@example.com
SEED_SUPER_ADMIN_NAME=Admin
SEED_SUPER_ADMIN_PASSWORD=changeme
```

### Docker

```bash
docker build -t ai-dam .
docker run -p 7860:7860 --env-file backend/.env ai-dam
```

## Project Structure

```
ai-dam/
├── backend/
│   ├── app/
│   │   ├── ai/          # AI pipelines, embeddings, tagging, retrieval
│   │   ├── api/         # FastAPI routes and dependencies
│   │   ├── core/        # Config, security, auth
│   │   ├── db/          # Database session, migrations, seeds
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic services
│   │   ├── utils/       # Helpers and utilities
│   │   └── main.py      # App entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/         # Axios client
│   │   ├── components/  # Reusable UI components
│   │   ├── context/     # React context providers
│   │   ├── pages/       # Page components by role
│   │   ├── styles/      # Global CSS
│   │   └── utils/       # Frontend utilities
│   └── package.json
└── Dockerfile
```

## License

Proprietary — All rights reserved.
