from pydantic_settings import BaseSettings
from pathlib import Path
import os
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Admin Dashboard API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Database - PostgreSQL (from .env file) or fallback to SQLite
    DATABASE_URL: str = "sqlite:///./lcrpay.db"

    # JWT Settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=180, description="Access token expiry in minutes (3 hours)")

    # Admin Credentials - MUST be set in .env file
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    # Upload/Static file settings
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    STATIC_URL_PATH: str = os.getenv("STATIC_URL_PATH", "/uploads")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields

# Initialize settings
try:
    settings = Settings()
    print(f"✅ Configuration loaded successfully")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print(f"⚠️  Please check your .env file. Copy from .env.example if needed.")
    raise

# Override DATABASE_URL from environment if provided
if os.getenv("DATABASE_URL"):
    settings.DATABASE_URL = os.getenv("DATABASE_URL")
    # Mask password in logs for security
    masked_url = settings.DATABASE_URL.split('@')[0] + '@****' if '@' in settings.DATABASE_URL else settings.DATABASE_URL
    print(f"✅ Using PostgreSQL: {masked_url}")
else:
    print(f"⚠️  Using SQLite (Local Development): {settings.DATABASE_URL}")
    print(f"💡 For PostgreSQL, set DATABASE_URL in .env file")