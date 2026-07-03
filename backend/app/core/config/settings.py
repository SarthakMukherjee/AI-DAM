from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # -----------------------------------
    # DATABASE
    # -----------------------------------

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # -----------------------------------
    # APP
    # -----------------------------------

    APP_NAME: str
    STORAGE_PATH: str

    # -----------------------------------
    # GROQ
    # -----------------------------------

    GROQ_API_KEY: str = Field(
        ...,
        env="GROQ_API_KEY"
    )

    # -----------------------------------
    # JWT
    # -----------------------------------

    JWT_SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"

    # -----------------------------------
    # CLOUDINARY
    # -----------------------------------

    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    # -----------------------------------
    # STORAGE BACKEND ("local", "cloudinary", "s3")
    # -----------------------------------

    STORAGE_BACKEND: str = "local"

    # -----------------------------------
    # OCR
    # -----------------------------------

    TESSERACT_CMD: str | None = None
    
    # -----------------------------------
    # admin
    # -----------------------------------
    seed_super_admin_email: str
    seed_super_admin_name: str
    seed_super_admin_password: str

    class Config:
        env_file = ".env"


settings = Settings()