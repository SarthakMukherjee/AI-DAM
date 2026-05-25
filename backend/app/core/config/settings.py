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

    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")

    # -----------------------------------
    # JWT
    # -----------------------------------

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # -----------------------------------
    # CLOUDINARY
    # -----------------------------------

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()