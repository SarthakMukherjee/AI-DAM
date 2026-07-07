from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes.asset_routes import router as asset_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.admin_routes import router as admin_router
from app.api.routes.reviewer_routes import router as reviewer_router
from app.api.routes.super_admin_routes import router as super_admin_router
from app.api.routes.search_routes import router as search_router

from app.db.session.database import Base, engine
from app.db.migrate import upgrade_db_schema
from app.services.storage.storage_initializer import initialize_storage

# -----------------------------------
# CREATE ALL TABLES
# -----------------------------------
from app.models.asset.asset_placement_model import AssetPlacement
from app.models.audit.audit_log_model import AuditLog

Base.metadata.create_all(bind=engine)

# Self-healing column migrations (safe to run on every startup)
try:
    upgrade_db_schema()
except Exception as _migrate_err:
    print(f"[MIGRATE] Non-fatal error during schema upgrade: {_migrate_err}")

initialize_storage()

# -----------------------------------
# RATE LIMITER
# -----------------------------------

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI DAM SYSTEM")

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(SlowAPIMiddleware)

# -----------------------------------
# CORS
# locked to frontend origin only
# credentials=True required for
# httpOnly cookie to work
# -----------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://ai-dam-six.vercel.app",
    "https://ai-dam-git-main-sarthak-ve-s-projects.vercel.app",
    "https://ai-idaigqetz-sarthak-ve-s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# ROUTERS
# -----------------------------------

app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(admin_router)
app.include_router(reviewer_router)
app.include_router(super_admin_router)
app.include_router(search_router)


@app.get("/")
def root():
    return {
        "message": "AI-DAM SYSTEM RUNNING"
    }