from fastapi import FastAPI

from app.api.routes.asset_routes import router as asset_router

from app.db.session.database import Base, engine

from app.services.storage.storage_initializer import (
    initialize_storage
)

Base.metadata.create_all(bind=engine)

initialize_storage()

app_dam = FastAPI(
    title="AI DAM SYSTEM"
)

app_dam.include_router(asset_router)


@app_dam.get("/")
def root():
    return {
        "message": "AI-DAM SYSTEM RUNNING"
    }