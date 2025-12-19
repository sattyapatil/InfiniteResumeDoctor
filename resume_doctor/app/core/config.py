import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Resume Doctor API"
    API_V1_STR: str = "/api/v1"
    
    # Core API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION: bool = ENVIRONMENT == "production"
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    # Allowed Origins for additional validation (stricter than CORS)
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    
    # File Upload Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Startup validation
if not settings.GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY is not set!")
else:
    print(f"✅ GEMINI_API_KEY loaded (starts with {settings.GEMINI_API_KEY[:4]}...)")

if settings.IS_PRODUCTION:
    if settings.API_SECRET_KEY == "dev-secret-key-change-in-production":
        print("🚨 CRITICAL: API_SECRET_KEY must be changed in production!")
    else:
        print(f"✅ API_SECRET_KEY configured for production")
    print(f"🔒 CORS Origins: {settings.cors_origins_list}")
else:
    print(f"🔧 Running in development mode (CORS: {settings.CORS_ORIGINS})")

