import os


class Settings:
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "Organization Management Service"
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "org_service")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me_in_production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
