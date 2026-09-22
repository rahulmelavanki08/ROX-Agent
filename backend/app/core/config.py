import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Automatically load environment variables from .env files
load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(BASE_DIR.parent / ".env", override=True)
STORAGE_DIR = BASE_DIR / 'storage'
SAMPLE_DOCS_DIR = BASE_DIR / 'sample_docs'

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR / 'uploads', exist_ok=True)
os.makedirs(STORAGE_DIR / 'adapted', exist_ok=True)
os.makedirs(STORAGE_DIR / 'applications', exist_ok=True)

class Settings(BaseModel):
    APP_NAME: str = 'ROX - Evidence-Gated Application Agent'
    API_PREFIX: str = '/api/v1'
    PORT: int = 8000
    PORTAL_PORT: int = 8000
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    MAX_RECOVERY_ATTEMPTS: int = 3
    STORAGE_DIR: Path = STORAGE_DIR
    SAMPLE_DOCS_DIR: Path = SAMPLE_DOCS_DIR

settings = Settings()
