import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Resume Doctor API"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

settings = Settings()

if not settings.GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set in environment variables!")
else:
    print(f"INFO: GEMINI_API_KEY loaded (starts with {settings.GEMINI_API_KEY[:4]}...)")
