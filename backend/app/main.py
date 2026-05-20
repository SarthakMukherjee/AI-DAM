from fastapi import FastAPI

from app.api.routes.asset_routes import router as asset_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.admin_routes import router as admin_router
from app.api.routes.reviewer_routes import router as reviewer_router
from app.api.routes.super_admin_routes import router as super_admin_router

from app.db.session.database import Base, engine

from app.services.storage.storage_initializer import (
    initialize_storage
)

# -----------------------------------
# CREATE ALL TABLES
# -----------------------------------

Base.metadata.create_all(bind=engine)

initialize_storage()

app = FastAPI(
    title="AI DAM SYSTEM"
)

# -----------------------------------
# ROUTERS
# -----------------------------------

app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(admin_router)
app.include_router(reviewer_router)
app.include_router(super_admin_router)


@app.get("/")
def root():
    return {
        "message": "AI-DAM SYSTEM RUNNING"
    }