from pydantic_settings import BaseSettings
import os

# Fix for Google scope mismatch during token exchange
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


class Settings(BaseSettings):
    SECRET_KEY: str  # Must be set in environment
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str # Must be set in environment
    FILE_STORAGE_BACKEND: str = "local"
    FILE_STORAGE_DIR: str = "uploads"
    FILE_STORAGE_BASE_URL: str | None = "/uploads"
    FILE_STORAGE_BUCKET: str | None = None
    FILE_STORAGE_S3_ENDPOINT: str | None = None
    FILE_STORAGE_S3_REGION: str | None = None
    FILE_STORAGE_S3_ACCESS_KEY: str | None = None
    FILE_STORAGE_S3_SECRET_KEY: str | None = None
    LLM_PROVIDER: str = "gemini"  # "ollama" or "gemini"
    OLLAMA_MODEL: str = "icarus-v3"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = "http://localhost:3000"
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def cors_origins(self) -> list[str]:
        return self.BACKEND_CORS_ORIGINS

    class Config:
        env_file = ".env"


settings = Settings()
