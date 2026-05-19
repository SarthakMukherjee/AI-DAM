from pydantic_settings  import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    APP_NAME: str
    STORAGE_PATH: str
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")

    class Config:
        env_file = ".env"

settings = Settings()