from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./resume.db"
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "")
DIFY_IMPROVE_APP_ID = os.getenv("DIFY_IMPROVE_APP_ID", "")
DIFY_MATCH_APP_ID = os.getenv("DIFY_MATCH_APP_ID", "")


OCR_BASE_URL = os.getenv("OCR_BASE_URL", "")
OCR_API_KEY = os.getenv("OCR_API_KEY", "")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "400"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

ENV = os.getenv("ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")