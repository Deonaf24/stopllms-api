from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = (
        "12481a530d71bf17d3cccf6db99543c87643cc8a9bcaa914720ce728e763042d"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "postgresql+psycopg2://deon@localhost:5432/stopllms"
    FILE_STORAGE_BACKEND: str = "local"
    FILE_STORAGE_DIR: str = "uploads"
    FILE_STORAGE_BASE_URL: str | None = "/uploads"
    FILE_STORAGE_BUCKET: str | None = None
    FILE_STORAGE_S3_ENDPOINT: str | None = None
    FILE_STORAGE_S3_REGION: str | None = None
    FILE_STORAGE_S3_ACCESS_KEY: str | None = None
    FILE_STORAGE_S3_SECRET_KEY: str | None = None
    OLLAMA_MODEL: str = "llama3.1:8b"

    class Config:
        env_file = ".env"


settings = Settings()
