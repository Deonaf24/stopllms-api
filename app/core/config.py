from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = (
        "12481a530d71bf17d3cccf6db99543c87643cc8a9bcaa914720ce728e763042d"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"


settings = Settings()
